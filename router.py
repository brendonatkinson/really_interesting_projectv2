#  COSC364 Assignment 1
#  Brendon Atkinson & Callum Sinclair
#  20 March 2017

import socket
import select
import random
import packet
from entry import Entry

RIP_RESPONSE_COMMAND = 2
RIP_REQUEST_COMMAND = 1
RIP_VERSION = 2
RIP_INFINITY = 16


class Router(object):

    def __init__(self, config):
        
        #  Localhost Definition
        self.UDP_IP = "127.0.0.1"
        
        # Get the values from the config file.
        self.router_id = config[0]
        self.inputs = config[1]
        self.routing_table = config[2]
        self.serve_list = []
        self.scheduler = None
        self.distance_table = None
        self.trigger_suppress = False
        self.update_packet = packet.RIP_Packet(int(self.router_id), RIP_RESPONSE_COMMAND)

        # Create d(i, j) for bellman-ford algorithm
        self.init_bellman_ford()
        
        #  Bind input sockets (use the first neighbour socket for sending updates)
        for inputport in self.inputs:
            input_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            input_socket.setblocking(True)
            try:
                input_socket.bind((self.UDP_IP, int(inputport)))
            except socket.error:
                print("Couldn't bind port: " + str(inputport))
            input_socket.settimeout(0.1)
            self.serve_list.append(input_socket)
            print("Listening on port: " + inputport)
        
        # Socket for sending updates
        self.output_socket = self.serve_list[0]
        self.output_port = self.output_socket.getsockname()[1]

        # Internal packets used to decode recieved data
        self.rip_packet_decoder = packet.RIP_Packet(int(self.router_id), RIP_RESPONSE_COMMAND)
        self.udp_packet_decoder = packet.UDP_Packet(self.output_port, 0)

        # Ask for all routing tables
        request_packet = packet.RIP_Packet(int(self.router_id), RIP_REQUEST_COMMAND)
        for neighbour in self.routing_table:
            self.send_packet(neighbour.address, request_packet.pack(neighbour.address))

        print("Router Initalised")

    def init_bellman_ford(self):

        # Use a dictionairy with router id's as key and
        # initial distance as memorys
        self.distance_table = dict()

        for neighbour in self.routing_table:
            self.distance_table[int(neighbour.destination)] = neighbour.metric

    def read_input_ports(self):
        """Check for packets on all input ports"""
        # Find ready sockets
        # Timeout value set to one second
        ready_to_read, ready_to_write, in_error = select.select(self.serve_list, [], [], 1)
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
                    data_to_read = False

        return recieved_updates
            
    def send_packet(self, dest_socket, rip_packet):
        """Simple function to send a packet"""
        udp_packet = packet.UDP_Packet(self.output_port, dest_socket, rip_packet)

        #  Send a simple packet
        self.output_socket.sendto(udp_packet.pack(), (self.UDP_IP, dest_socket))

    def send_table(self):
        """Sends the entire routing table to neighbours"""
        print("Sending table update")

        # Schedule another unsolicted update
        self.scheduler.enter(30+random.randint(0, 5), 1, self.send_table, argument=())

        # Clear any triggered updates yet to be sent
        self.update_packet.clear()

        # Build the table entries packet
        rip_packet = packet.RIP_Packet(int(self.router_id), RIP_RESPONSE_COMMAND)
        for entry in self.routing_table:

            rip_packet.add_entry(entry)

        #  Send Response packets to each neighbour
        if rip_packet.entries:
            for neighbour in self.routing_table:
                self.send_packet(neighbour.address, rip_packet.pack(neighbour.address))

    def read_inputs(self):

        # Schedule another timer update at the start, so processing time is counted
        self.scheduler.enter(2, 9, self.read_inputs, argument=())

        #  Process response packets from neighbours
        data = self.read_input_ports()
        self.process_packets(data)

    def process_packets(self, data):
        """Decodes packet, checks if valid data, determines if update required"""
        # print("Processing")
        # Needs Error Checking

        if len(data) > 0:

            for datum in data:
                #  Packet Information
                received_data = datum

                # Decode UDP data
                udp_header, udp_data = self.udp_packet_decoder.unpack(received_data)
                # If errors in checksum, packet is dropped
                if udp_data:

                    # Decode RIP data
                    rip_data = self.rip_packet_decoder.unpack(udp_data)

                    # Get the RIP header data
                    header = rip_data[0]
                    received_id = header.router_id
                    print("Recieved Update from " + str(received_id))

                    # Get the routing table corresponding to the router packet received from
                    # If new route discovered, set the router as the next hop
                    next_hop_entry = None
                    for entry in self.routing_table:
                        if str(entry.destination) == str(received_id):
                            next_hop_entry = entry

                            # If router has returned from timeout, set it's distance to correct value
                            if self.distance_table[int(received_id)] < next_hop_entry.metric:
                                self.update_routing_entry(next_hop_entry,
                                                          next_hop_entry.address,
                                                          self.distance_table[int(received_id)],
                                                          next_hop_entry.destination)
                                self.update_packet.add_entry(next_hop_entry)

                    if next_hop_entry:

                        # If next hop entry is first hop, reset timeout
                        if (int(next_hop_entry.next_hop) == int(next_hop_entry.destination) and
                           int(next_hop_entry.destination) == int(received_id)):
                            self.reset_entry_timeout(next_hop_entry)

                        # Iterate through all the routing data information from the router
                        for advertised_destination in rip_data[1:]:

                            # Attempt to find a entry matching this advertised destination
                            routing_table_entry = None
                            for entry in self.routing_table:
                                # Check if entry already exists
                                if str(entry.destination) == str(advertised_destination.destination):
                                    routing_table_entry = entry

                            # Bellman Ford Algorithm
                            new_hop_cost = self.distance_table[int(received_id)] + advertised_destination.metric

                            # If entry exists, check if better route exists.
                            if routing_table_entry:

                                # Check if advertised destination has hop cost 16 indicating host unreachable
                                if (advertised_destination.metric >= RIP_INFINITY and advertised_destination.next_hop
                                        == routing_table_entry.destination and not routing_table_entry.expired_flag):
                                    # print("EXPIRING")
                                    routing_table_entry.expired()
                                    self.update_expired_entry(routing_table_entry,
                                                              next_hop_entry.address,
                                                              routing_table_entry.metric,
                                                              routing_table_entry.destination)
                                    self.update_packet.add_entry(routing_table_entry)

                                else:

                                    # Check for better hop route
                                    if new_hop_cost < routing_table_entry.metric:
                                        # print("Routing Table Entry Update")
                                        self.update_routing_entry(routing_table_entry,
                                                                    next_hop_entry.address,
                                                                    new_hop_cost,
                                                                    next_hop_entry.destination)
                                        self.update_packet.add_entry(routing_table_entry)

                                    if int(routing_table_entry.next_hop) == int(received_id):
                                        self.reset_entry_timeout(routing_table_entry)

                            # Create a routing entry
                            else:

                                # Ensure no routing entry created for itself or loop created
                                if (int(advertised_destination.destination) != int(self.router_id) and
                                        int(advertised_destination.next_hop != int(self.router_id))):

                                    if new_hop_cost >= RIP_INFINITY:
                                        new_hop_cost = RIP_INFINITY

                                    new_entry = Entry([advertised_destination.destination,
                                                        next_hop_entry.address,
                                                        new_hop_cost,
                                                        next_hop_entry.destination])
                                    self.routing_table.append(new_entry)
                                    self.update_packet.add_entry(new_entry)
                    # Neighbour returned from garbage collection
                    else:

                        # print("Restore from garbage collection")
                        new_entry = Entry([int(received_id),
                                           udp_header.src,
                                           int(self.distance_table[int(received_id)]),
                                           int(received_id)])
                        self.routing_table.append(new_entry)
                        self.update_packet.add_entry(new_entry)

            # Check if triggered update required

            if len(self.update_packet.entries) > 0 and not self.trigger_suppress:
                print("Sending Update")
                self.send_table_updates(self.update_packet)
                self.update_packet.clear()

                # Suppressed triggered updates for 1-5 seconds
                self.trigger_suppress = True
                self.scheduler.enter(random.randint(1, 5), 1, self.unsuppress, argument=())

    def send_table_updates(self, packet):

        for neighbour in self.routing_table:
            self.send_packet(neighbour.address, packet.pack(neighbour.address))

    def update_routing_entry(self, entry, address, new_cost, next_hop):
        # print("Updating routing entry for: " + str(entry.destination))
        if new_cost >= RIP_INFINITY:
            entry.metric = RIP_INFINITY
        else:
            entry.metric = new_cost
        entry.address = address
        entry.next_hop = next_hop
        entry.reset_timeout()

    def update_expired_entry(self, entry, address, new_cost, next_hop):
        # print("Updating routing entry for: " + str(entry.destination))
        if new_cost >= RIP_INFINITY:
            entry.metric = RIP_INFINITY
        else:
            entry.metric = new_cost
        entry.address = address
        entry.next_hop = next_hop

    def reset_entry_timeout(self, entry):
        entry.reset_timeout()

    def update_timers(self):
        """Update the routing table timers"""

        # Schedule another timer update at the start, so processing time is counted
        self.scheduler.enter(5, 1, self.update_timers, argument=())

        # Create a packet to send timeout updates
        rip_packet = packet.RIP_Packet(int(self.router_id), RIP_RESPONSE_COMMAND)

        # print("Timer update")
        for neighbour in self.routing_table:

            # Check if the route has already expired
            if neighbour.expired_flag:
                if neighbour.garbage_remaining() <= 0:

                    #  Removed route
                    print("Removing link to " + str(neighbour.destination))
                    self.routing_table.remove(neighbour)
            else:
                # Check if neighbour has timed out
                if neighbour.timeout_remaining() <= 0:
                    neighbour.expired()
                    self.run_bellman_ford(neighbour.destination, rip_packet)
                    rip_packet.add_entry(neighbour)

        if len(rip_packet.entries) > 0:
            print("Sending Update")
            self.send_table_updates(rip_packet)

    def run_bellman_ford(self, expired_id, packet):

        print("Purging all routes using " + str(expired_id))

        # Find the new best cost for each link in routing table
        for neighbour in self.routing_table:

            change_flag = False

            # Set the link initially to RIP Infinity
            if int(neighbour.next_hop) == int(expired_id) and int(neighbour.destination) != int(expired_id):
                self.update_routing_entry(neighbour,
                                          neighbour.address,
                                          RIP_INFINITY,
                                          expired_id)
                change_flag = True

            # If link is direct neighbour, set to known value
            if int(neighbour.destination) in self.distance_table and not neighbour.expired_flag:
                if self.distance_table[int(neighbour.destination)] < neighbour.metric:
                    self.update_routing_entry(neighbour,
                                              neighbour.address,
                                              self.distance_table[int(neighbour.destination)],
                                              neighbour.destination)
                    change_flag = True

            if change_flag:
                packet.add_entry(neighbour)
    
    def close_connections(self):
        
        # Close all sockets connections
        for sockets in self.serve_list:
            sockets.close()
        
        print("Closing connections")

    def unsuppress(self):
        self.trigger_suppress = False
        if len(self.update_packet.entries) > 0:
            print("Sending Update")
            self.send_table_updates(self.update_packet)
            self.update_packet.clear()

    def print_table(self):
        self.scheduler.enter(5, 2, self.print_table, argument=())
        # Implement table output
        print("Own ID: {0}".format(self.router_id))
        print(" ID ||First|Cost| Expired |Expiry |Garbage|")
        print("----++-----+----+---------+-------+-------+--")
        for entry in self.routing_table:
            print(" {:>2} || {:>3} | {:>2} | {:<7} | {:<1f} | {:<1f} |".format(entry.destination, entry.next_hop,
                                                                entry.metric, entry.expired_flag,
                                                                entry.timeout_remaining(), entry.garbage_remaining()))