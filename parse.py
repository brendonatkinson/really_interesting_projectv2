# COSC364 Assignment 1
# Brendon Atkinson & Callum Sinclair
# 20 March 2016

def build_table(config_file):
    # Opens config file, reads and returns routing table
    # @param config_file the filename of the configuration file

    #router id 1 <= x <= 64000, unique
    #set of port numbers to listen on (neighbours) format eg input-ports 6110, 6201, 7345
        #port numbers 1024 <= x <= 64000
    #output ports: portnum-linkmetric-routerid eg. outputs 5000-1-1, 5002-5-4
        # port numbers 1024 <= x <= 64000, metric 0 >= x >= 16 (Double check this)
        # no outputs should also be inputs

    raise NotImplementedError