#  COSC364 Assignment 1
#  Brendon Atkinson & Callum Sinclair
#  20 March 2017

import socket
import select
import time
import random
import packet

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
            # Max Packet Size = 504 Bytes / 4032 Bits
            # Not reading all packet data here
            data_to_read = True
            while data_to_read:
                try:
                    data, addr = input_socket.recvfrom(4032)
                    recieved_updates.append(data)
                except socket.error:
                    """Catching socket.timeout does not work correctly"""
                    data_to_read = False

        return recieved_updates
            
    def send_packet(self, destination_address, rip_packet):
        """Simple function to send a packet"""
        #  Debugging output
        print("sending to " + str(destination_address))
        
        #  Send a simple packet
        self.output_socket.sendto(rip_packet, (self.UDP_IP, destination_address))

    def send_table(self):
        """Sends the entire routing table to neighbours"""
        print("Sending table update")

        # Build the table entries packet
        rip_packet = packet.Packet(int(self.router_id), RIP_RESPONSE_COMMAND)
        for entry in self.routing_table:
            rip_packet.add_entry(entry)

        #  Send Response packets to each neighbour
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

            for datum in data:
                # UDP Packet Information
                rip_data = datum

                # Create a packet object to decode data correctly
                rip_packet = packet.Packet(int(self.router_id), RIP_RESPONSE_COMMAND)
                rip_data = rip_packet.unpack(rip_data)

                # Get the RIP header data
                header = rip_data[0]
                recieved_id = header.router_id
                print("Recieved Update from " + str(recieved_id))

                # Get the routing table corresponding to the router packet recieved from
                recieved_entry = None
                for routing_entry in self.routing_table:
                    if str(routing_entry.destination) == str(recieved_id):
                        recieved_entry = routing_entry

                # Iterate through all the routing data information
                for entry in rip_data[1:]:

                    # Get the routing table corresponding to this entry
                    rip_entry = None
                    for routing_entry in self.routing_table:
                        if str(routing_entry.destination) == str(entry.destination):
                            rip_entry = routing_entry

                    if not rip_entry:

                        # Debugging
                        # print("Router: " + str(entry.destination))
                        # print("Cost: " + str(entry.metric))
                        print("Hop: " + str(recieved_entry.metric))
                        # print("Cost + Hop: " + str(entry.metric + recieved_entry.metric))
                        # print("Current Best :" + str(rip_entry.metric))

                        # Check if lower cost route, update and sen
                        if (entry.metric + recieved_entry.metric) < rip_entry.metric:
                            print("Updating Entry")
                            self.update_routing_entry(rip_entry, (entry.metric + recieved_entry.metric), recieved_id)
                            rip_packet.add_entry(rip_entry)

            # Check if triggered update required

            # Is this meant to occur as soon as update or leave here?
            if len(rip_packet.entries) > 0:
                print("Update required")
                self.send_triggered_update(rip_packet.pack())

    def send_triggered_update(self, packet):

        for neighbour in self.routing_table:
            self.send_packet(neighbour.address, packet)
     
    def update_routing_entry(self, entry, new_cost, next_hop):
        # print("Updating routing entry for: " + str(entry.destination))
        entry.metric = new_cost
        entry.next_hop = next_hop
        entry.reset_timeout()

    def update_timers(self):
        """Update the routing table timers"""

        # Schedule another timer update at the start, so processing time is counted
        self.scheduler.enter(5, 1, self.update_timers, argument=())

        # print("Timer update")
        for neighbour in self.routing_table:
            if neighbour.timeout_remainin() <= 0:
                neighbour.expired()
            if neighbour.expired_flag:
                garbage_time = time.time() - neighbour.garbage
                if garbage_time <= 0:
                    #  Removed route
                    self.routing_table.remove(neighbour)

        # Trigger update here ...?
    
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
            print(" {:>2} || {:>3} | {:>2} | {:<7} | {:<8} | {:<8} |".format(entry.destination, entry.address,
                                                                             entry.metric, entry.expired_flag,
                                                                             entry.timeout_remaining(), entry.garbage))