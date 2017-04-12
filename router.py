# COSC364 Assignment 1
# Brendon Atkinson & Callum Sinclair
# 20 March 2017

import socket
import select
import time
import random


class Router(object):

    def __init__(self, config):
        
        # Localhost Definition
        self.UDP_IP = "127.0.0.1"
        
        # Get the values from the config file.
        self.routerid = config[0]
        self.neighbours = config[1]
        self.routing_table = config[2]
        self.serve_list = []
        self.scheduler = None
        
        # Bind input sockets (use the first neighbour socket for sending updates)
        for neighbour_port in self.neighbours:
            neighbour_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            neighbour_socket.setblocking(True)
            neighbour_socket.bind((self.UDP_IP, int(neighbour_port)))
            self.serve_list.append(neighbour_socket)
            print("Listening on port: " + neighbour_port)
        
        #Socket for sending updates
        self.output_socket = self.serve_list[0]
        
        
        print("Router Initalised")

    # Check all input ports for a packet
    def read_input_ports(self):
        
        # Find ready sockets
        # Timeout value set to one second
        ready_to_read, ready_to_write, in_error = select.select(self.serve_list,
                                                                [],
                                                                [],
                                                                1)
        recieved_updates = []
        for sockets in ready_to_read:
            # Buffer Size = 1024
            data, address = sockets.recvfrom(1024)
            recieved_updates.append((address, data))

        return recieved_updates
            
    # Simple function to send a packet
    def send_packet(self, destination_address, rip_type):
        
        # Simple message
        message = bytes("Hello", 'utf-8')
        print("sending to " + str(destination_address))
        
        # Send a simple packet
        self.output_socket.sendto(message, (self.UDP_IP, destination_address))

    def send_table(self):
        print("Sending table update")

        # Send Response packets to each neighbour (unsolicited)
        rip_type = "response"
        for neighbour in self.routing_table:
            self.send_packet(neighbour.address, rip_type)

        # Process response packets from neighbours
        data = self.read_input_ports()
        self.process_packets(data)
        
        #Schedule another unsolicted update
        self.scheduler.enter(30+random.randint(0,5), 1, self.send_table, argument=())

    def process_packets(self, data):
        print("Processing: ")
        print(data)
        # To Do
        # Check validity of packets (ip, port, values, flags, e.t.c)
        # If valid:
        # Update information in table if better than existing information
        # Send Poison - Reverse packets
        # Else
        # Ignore

    def update_timers(self):
        print("Timer update")

        for neighbour in self.routing_table:
            curr_timeout = time.time() - neighbour.timeout
            if curr_timeout >= 0:
                neighbour.expired()
                # triggered update?
                # poison reverse?
            if neighbour.expired_flag:
                garbage_time = time.time() - neighbour.garbage
                if garbage_time <= 0:
                    # Removed route
                    self.routing_table.remove(neighbour)

        # Schedule another timer update
        self.scheduler.enter(5, 1, self.update_timers, argument=())
    
    def close_connections(self):
        
        # Close all sockets connections
        for sockets in self.serve_list:
            sockets.close()
        
        print("Closing connections")