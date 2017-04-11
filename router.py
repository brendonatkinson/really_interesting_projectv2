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
    # Needs to be implemented
    def send_packet(self, destination_entry, type):
        
        # Simple message
        message = bytes("Hello", 'utf-8')
        port_to_send = self.routing_table[0][1]
        print("sending to " + str(port_to_send))
        
        # Send a simple packet
        self.serve_list[0].sendto(message, (self.UDP_IP, port_to_send))

    def send_table(self):
        print("Sending table update")

        # Send Response packets to each neighbour (unsolicited)
        type = "response"
        for neighbour in self.routing_table:
            self.send_packet(neighbour, type)

        # Process response packets from neighbours
        data = self.read_input_ports()
        self.process_packets(data)

        #Schedule another unsolicted update
        self.scheduler.enter(30+random.randint(0,5), 1, self.send_table, argument=())

    def process_packets(data):
        None
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