# COSC364 Assignment 1
# Brendon Atkinson & Callum Sinclair
# 12 April 2017
import entry
import struct
import socket

RIP_HEADER_SIZE = 4
RIP_ENTRY_SIZE = 20

class Packet(object):
    
    def __init__(self, router_id, command, version = 2):
        
        self.command = command
        self.version = version
        self.router_id = router_id
        self.entries = []
        
    def add_entry(self, entry):
        
        self.entries.append(entry)
        
    def remove_entry(self, entry):
        
        self.entries.remove(entry)
        
    def pack(self):
        
        #Build the header
        data = struct.pack('!BBH', self.command, self.version, self.router_id)
        
        #Build the routing table entries
        #TODO: Not sure this is the information we must be sending
        for entry in self.entries:
            data += struct.pack('!HHIIII', 2, int(entry.destination),
                                int(entry.next_hop), 0, 0, int(entry.metric))
        
        return data
    
    def unpack(self, data):
        
        #Unpack the header
        header = struct.unpack("!BBH", data[:RIP_HEADER_SIZE])
        
        #Print header for debugging
        print("--- Header --- ")
        print("Command: " + str(header[0]))
        print("Version: " + str(header[1]))
        print("Router ID: " + str(header[2]))
        
        #Unpack the entries individually
        entries_data = data[RIP_HEADER_SIZE:]
        entries = [entries_data[i: i + RIP_ENTRY_SIZE] for i in range(0, len(entries_data), RIP_ENTRY_SIZE)]
        
        #Print entries for debugging
        for entry in entries:
            
            data = struct.unpack("!HHIIII", entry)
            print("--- ENTRY ---")
            print("AFI: " + str(data[0]))
            print("Router To: " + str(data[1]))
            print("Next Hop: " + str(data[2]))
            print("Must Be Zero: " + str(data[3]))
            print("Must Be Zero: " + str(data[4]))
            print("Metric: " + str(data[5]))            