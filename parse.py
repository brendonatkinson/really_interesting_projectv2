# COSC364 Assignment 1
# Brendon Atkinson & Callum Sinclair
# 20 March 2016

def build_table(config_file):
    # Opens config file, reads and returns routerid, input ports, routing table
    # @param config_file the filename of the configuration file

    temp = []
    inputstream = open(config_file, 'r')
    for line in lines(inputstream):
        temp.append(line.split(', '))

    #Verify router ID
    routerid = temp.pop(0)
    if not ('router-id' in routerid) and (int(routerid[1]) in range(1,64000)):
        raise Exception

    #Verify input ports
    input_ports = temp.pop(0)
    if 'input-ports' in input_ports.pop(0):
        for port in input_ports:
            if int(port) not in range(1024,64000):
                raise Exception

    # Build routing table
    # Layout of this table is [ID, PORT ,COST,FLAG,TIMER]
    output_ports = temp.pop(0)
    routing_table = []
    flag = False
    timer = [0,0]
    for entry in output_ports[1:]:
        entry = entry.split('-')
        if verify_output(routerid, input_ports, entry):
            id = entry[2]
            port = int(entry[0])
            cost = int(entry[1])
            routing_table.append([entry[2],int(entry[0]),int(entry[1]), flag, timer])
    return routerid[1], input_ports, routing_table


def lines(f):
    # Helper function
    # Removes blank lines and comments

    for l in f:
        line = l.rstrip()
        if (line) and (line[0] != '#'):
            yield line


def verify_output(ownid, input_ports, entry):
    # ID is unique
    if entry[2] == ownid[0]:
        raise Exception
    # Ports are not input ports and 1024 <= x <= 64000
    if (entry[0] in input_ports) and (int(entry[0]) not in range(1024,64000)):
        raise Exception
    # Cost is valid
    if int(entry[1]) not in range(0,16):
        raise Exception
    return True
