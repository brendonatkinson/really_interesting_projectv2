import router
import sys
import time
from parse import build_table

if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("No config file present")
    
    else:
        #Build the router from the conifg file 
        config = build_table(sys.argv[1])
        router = router.Router(config)
        #Enter infinite loop
        while True:
            None
            # Every 30 seconds
                # Send Response Packets to all neighbours(unsolicited)
                # Process response packets from neighbours
                    # Check validity of packets (ip, port, values, flags, e.t.c)
                    # If valid:
                        # Update information in table if better than existing information
                        # Send Poison - Reverse packets
                    # Else
                        # Ignore
            # For each neighbour
                # Start timer since last packet received
                # If time since exceeds threshold:
                    # Begin garbage timeout
                    # Set path to infinity
                    # Send Triggered Packet Updates
                    # Send Poison - Reverse packets
                # If time since exceeds garbage timeout
                    # Remove route from forwarding table

            router.send_packet()
            time.sleep(1)
            router.read_input_ports()
            
        #Never reaches here
        router.close_connections()
        