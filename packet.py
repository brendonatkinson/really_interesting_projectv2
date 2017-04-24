# COSC364 Assignment 1
# Brendon Atkinson & Callum Sinclair
# 12 April 2017
import entry
import struct
import socket
import hashlib


UDP_HEADER_FORMAT = '!HHH16s'
UDP_HEADER_SIZE = 22

RIP_HEADER_SIZE = 4
RIP_HEADER_FORMAT = '!BBH'
RIP_ENTRY_SIZE = 20
RIP_ENTRY_FORMAT = '!HHIIII'
RIP_INFINITY = 16

class RIP_Packet(object):
    
    def __init__(self, router_id, command, version = 2):
        
        self.command = command
        self.version = version
        self.router_id = router_id
        self.entries = []
        
    def add_entry(self, entry):
        
        self.entries.append(entry)
        
    def remove_entry(self, entry):
        
        self.entries.remove(entry)
        
    def pack(self, address):
        
        # Build the header
        data = struct.pack(RIP_HEADER_FORMAT, self.command, self.version, self.router_id)

        # Build the routing table entries
        for entry in self.entries:

            # Poison reverse, any destinations achievable via this neighbour, set metric to infinity
            metric = entry.metric
            if entry.address == address:
                metric = RIP_INFINITY

            data += struct.pack(RIP_ENTRY_FORMAT, int(socket.AF_INET), int(entry.destination),
                                int(entry.next_hop), 0, 0, int(metric))
        
        return data
    
    def unpack(self, data):
        
        decoded_data = []
        
        #Unpack the header
        header = struct.unpack(RIP_HEADER_FORMAT, data[:RIP_HEADER_SIZE])
        decoded_data.append(Header_Data_RIP(header[2], header[0], header[1]))
        
        #Print header for debugging
        #print("--- Header --- ")
        #print("Command: " + str(header[0]))
        #print("Version: " + str(header[1]))
        #print("Router ID: " + str(header[2]))
        
        #Unpack the entries individually
        entries_data = data[RIP_HEADER_SIZE:]
        entries = [entries_data[i: i + RIP_ENTRY_SIZE] for i in range(0, len(entries_data), RIP_ENTRY_SIZE)]
        
        #Print entries for debugging
        for entry in entries:
            
            data = struct.unpack(RIP_ENTRY_FORMAT, entry)
            #List Order: AFI, Destination, Next Hop, Metric
            decoded_data.append(Packet_Data_RIP(data[0], data[1], data[2], data[5]))
            #print("--- ENTRY ---")
            #print("AFI: " + str(data[0]))
            #print("Router To: " + str(data[1]))
            #print("Next Hop: " + str(data[2]))
            #print("Must Be Zero: " + str(data[3]))
            #print("Must Be Zero: " + str(data[4]))
            #print("Metric: " + str(data[5]))
        
        return decoded_data

class UDP_Packet(object):

    def __init__(self, src, dest, data=""):

        self.data = data
        self.data_len = len(data)
        self.src = src
        self.dest = dest

    def pack(self):

        #Specify a regex for the size of data
        regex = UDP_HEADER_FORMAT + str(self.data_len) + 's'
        #Compute the checksum
        checksum = hashlib.md5(self.data).digest()
        packet = struct.pack(regex, self.src, self.dest, self.data_len, checksum, self.data)

        return packet

    def unpack(self, data):
        udp = struct.unpack(UDP_HEADER_FORMAT, data[:UDP_HEADER_SIZE])
        udp_header = Header_Data_UDP(udp[0], udp[1], udp[2], udp[3])

        data_regex = str(udp_header.data_len) + 's'
        udp_data = struct.unpack(data_regex, data[UDP_HEADER_SIZE:])

        #Recompute the checksum
        checksum = hashlib.md5(udp_data[0]).digest()
        if (checksum == udp_header.checksum):
            return udp_data[0]
        else:
            print("Checksum incorrect, dropping data!")
            return None

class Header_Data_UDP(object):

    def __init__(self, src, dest, data_len, checksum):

        self.src = src
        self.dest = dest
        self.data_len = data_len
        self.checksum = checksum

class Packet_Data_RIP(object):
    
    def __init__(self, afi, destination, next_hop, metric):
        
        self.afi = afi
        self.destination = destination
        self.next_hop = next_hop
        self.metric = metric
        
class Header_Data_RIP(object):
    
    def __init__(self, router_id, command, version):
        
        self.command = command
        self.version = version 
        self.router_id = router_id