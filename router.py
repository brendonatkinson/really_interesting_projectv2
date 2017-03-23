import socket
import select

class Router(object):
    
    def __init__(self, config):
        
        #Localhost Definition
        self.UDP_IP = "127.0.0.1"
        
        #Get the values from the config file.
        self.routerid = config[0]
        self.neighbours = config[1]
        self.routing_table = config[2]
        
        self.serve_list = []
        
        #Bind input sockets (use the first neighbour socket for sending updates)
        for neighbour_port in self.neighbours:
            neighbour_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            neighbour_socket.setblocking(True)
            neighbour_socket.bind((self.UDP_IP, int(neighbour_port)))
            self.serve_list.append(neighbour_socket)
            print("Listening on port: " + neighbour_port)
        
        print("Router Initalised")
        
        
    
    #Check all input ports for a packet
    def read_input_ports(self):
        
        #Find ready sockets
        #Timeout value set to one second
        ready_to_read, ready_to_write, in_error = select.select(self.serve_list,
                                                                [],
                                                                [],
                                                                1)
        for socket in ready_to_read:
            #Buffer Size = 1024
            data, addr = socket.recvfrom(1024)
            print(data)
            
    #Simple function to send a packet        
    def send_packet(self):
        
        #Simple message
        message = bytes("Hello", 'utf-8')
        port_to_send = self.routing_table[0][1]
        print("sending to " + str(port_to_send))
        
        #Send a simple packet
        self.serve_list[0].sendto(message,(self.UDP_IP, port_to_send))
        
    
    def close_connections(self):
        
        #Close all sockets connections
        for socket in self.serve_list:
            socket.close()
        
        print("Closing connections")