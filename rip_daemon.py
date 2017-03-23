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
            router.send_packet()
            time.sleep(1)
            router.read_input_ports()
            
        #Never reaches here
        router.close_connections()
        