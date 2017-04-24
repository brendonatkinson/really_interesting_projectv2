#  COSC364 Assignment 1
#  Brendon Atkinson & Callum Sinclair
#  20 March 2017

import socket
import select
import random
import packet
import entry

RIP_RESPONSE_COMMAND = 2
RIP_VERSION = 2


class Router(object):

    def __init__(self, config):
        
        #  Localhost Definition
        self.UDP_IP = "127.0.0.1"
        
        #  Get the values from the config file.
        self.router_id = config[0]
        self.inputs = config[1]
        self.routing_table = config[2]
        self.serve_list = []
        self.scheduler = None
        
        #  Bind input sockets (use the first neighbour socket for sending updates)
        for inputport in self.inputs:
            input_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            input_socket.setblocking(True)
            input_socket.bind((self.UDP_IP, int(inputport)))
            input_socket.settimeout(0.1)
            self.serve_list.append(input_socket)
            print("Listening on port: " + inputport)
        
        # Socket for sending updates
        self.output_socket = self.serve_list[0]
        self.output_port = self.output_socket.getsockname()[1]

        #Internal packets used to decode recieved data
        self.rip_packet_decoder = packet.RIP_Packet(int(self.router_id), RIP_RESPONSE_COMMAND)
        self.udp_packet_decoder = packet.UDP_Packet(self.output_port, 0)

        print("Router Initalised")

    def read_input_ports(self):
        """Check for packets on all input ports"""
        #  Find ready sockets
        #  Timeout value set to one second
        ready_to_read, ready_to_write, in_error = select.select(self.serve_list,
                                                                [],
                                                                [],
                                                                1)
        recieved_updates = []
        for input_socket in ready_to_read:
            # Max RIP Packet Size = 504 Bytes / 4032 Bits
            # UDP Packet Size = 22 Bytes / 176 bits
            # Max Packet Size = 526 / 4208 Bits
            # Not reading all packet data here
            data_to_read = True
            while data_to_read:
                try:
                    data, addr = input_socket.recvfrom(4208)
                    recieved_updates.append(data)
                except socket.error:
                    """Catching socket.timeout does not work correctly"""
                    data_to_read = False

        return recieved_updates
            
    def send_packet(self, dest_socket, rip_packet):
        """Simple function to send a packet"""
        #  Debugging output
        print("sending to " + str(dest_socket))

        udp_packet = packet.UDP_Packet(self.output_port, dest_socket, rip_packet)

        #  Send a simple packet
        self.output_socket.sendto(udp_packet.pack(), (self.UDP_IP, dest_socket))

    def send_table(self):
        """Sends the entire routing table to neighbours"""
        print("Sending table update")

        # Build the table entries packet
        rip_packet = packet.RIP_Packet(int(self.router_id), RIP_RESPONSE_COMMAND)
        for entry in self.routing_table:
            rip_packet.add_entry(entry)

        #  Send Response packets to each neighbour
        if rip_packet.entries:
            for neighbour in self.routing_table:
                self.send_packet(neighbour.address, rip_packet.pack(neighbour.address))

        #  Process response packets from neighbours
        data = self.read_input_ports()
        self.process_packets(data)
        
        # Schedule another unsolicted update
        self.scheduler.enter(30+random.randint(0, 5), 1, self.send_table, argument=())

    def process_packets(self, data):
        """Decodes packet, checks if valid data, determines if update required"""
        print("Processing")
        # Needs Error Checking

        if len(data) > 0:

            # Create a rip packet if updates required
            rip_packet = packet.RIP_Packet(int(self.router_id), RIP_RESPONSE_COMMAND)

            for datum in data:
                #  Packet Information
                recieved_data = datum

                # Decode UDP data
                udp_data = self.udp_packet_decoder.unpack(recieved_data)
                # If error's in checksum, packet is dropped
                if (udp_data != None):

                    # Decode RIP data
                    rip_data = self.rip_packet_decoder.unpack(udp_data)

                    # Get the RIP header data
                    header = rip_data[0]
                    recieved_id = header.router_id
                    print("Recieved Update from " + str(recieved_id))

                    # Get the routing table corresponding to the router packet recieved from
                    physical_router_entry = None
                    for routing_entry in self.routing_table:
                        if str(routing_entry.destination) == str(recieved_id):
                            physical_router_entry = routing_entry
                            self.reset_entry_timeout(physical_router_entry)

                    # Iterate through all the routing data information
                    for advertised_route in rip_data[1:]:
                        # Get the routing table corresponding to this entry
                        rip_entry = None
                        for routing_entry in self.routing_table:
                            #Check if entry already exists
                            if str(routing_entry.destination) == str(advertised_route.destination):
                                rip_entry = routing_entry

                        # If entry exists, check if better route exists.
                        if rip_entry != None:
                            # Check for better hop route
                            if (advertised_route.metric + physical_router_entry.metric) < rip_entry.metric:
                                print("Updating Entry")
                                self.update_routing_entry(rip_entry, (advertised_route.metric + physical_router_entry.metric), recieved_id)
                                rip_packet.add_entry(rip_entry)

                            else:
                                hop_cost = advertised_route.metric + physical_router_entry.metric
                                if (rip_entry.destination == advertised_route.destination and
                                    hop_cost == rip_entry.metric):
                                    self.reset_entry_timeout(rip_entry)

                        # Create routing entry
                        else:
                            if (int(advertised_route.destination) != int(self.router_id)):
                                link_cost = advertised_route.metric + physical_router_entry.metric
                                self.routing_table.append(entry.Entry([advertised_route.destination, physical_router_entry.address,
                                                                      link_cost,
                                                                      physical_router_entry.destination]))


            # Check if triggered update required

            # Is this meant to occur as soon as update or leave here?
            if len(rip_packet.entries) > 0:
                print("Update required")
                self.send_table_updates(rip_packet)

    def send_table_updates(self, packet):

        for neighbour in self.routing_table:
            self.send_packet(neighbour.address, packet.pack(neighbour.address))
     
    def update_routing_entry(self, entry, new_cost, next_hop):
        # print("Updating routing entry for: " + str(entry.destination))
        entry.metric = new_cost
        entry.next_hop = next_hop
        entry.reset_timeout()

    def reset_entry_timeout(self, entry):
        entry.reset_timeout()

    def update_timers(self):
        """Update the routing table timers"""

        # Schedule another timer update at the start, so processing time is counted
        self.scheduler.enter(5, 1, self.update_timers, argument=())

        #Create a packet to send timeout updates
        rip_packet = packet.RIP_Packet(int(self.router_id), RIP_RESPONSE_COMMAND)

        # print("Timer update")
        for neighbour in self.routing_table:

            if neighbour.expired_flag:
                if neighbour.garbage_remaining() <= 0:
                    #  Removed route
                    print("Removing link to " + str(neighbour.destination))
                    self.routing_table.remove(neighbour)
            else:
                if neighbour.timeout_remaining() <= 0:
                    # Neighbour has timed out
                    neighbour.expired()
                    # Reset all links which used this as next hop:
                    rip_packet.add_entry(neighbour)

        if len(rip_packet.entries) > 0:
            print("Timeout related update required")
            self.send_table_updates(rip_packet)



    
    def close_connections(self):
        
        # Close all sockets connections
        for sockets in self.serve_list:
            sockets.close()
        
        print("Closing connections")

    def print_table(self):
        self.scheduler.enter(10, 2, self.print_table, argument=())
        # Implement table output
        print("Own ID: {0}".format(self.router_id))
        print(" ID ||First|Cost| Expired |Expiry |Garbage|")
        print("----++-----+----+---------+-------+-------+--")
        for entry in self.routing_table:
            print(" {:>2} || {:>3} | {:>2} | {:<7} | {:<1f} | {:<1f} |".format(entry.destination, entry.next_hop,
                                                                             entry.metric, entry.expired_flag,
                                                                             entry.timeout_remaining(), entry.garbage_remaining()))