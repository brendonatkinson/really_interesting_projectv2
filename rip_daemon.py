# COSC364 Assignment 1
# Brendon Atkinson & Callum Sinclair
# 23 March 2017

import router
import sys
import sched, time, random
from parse import build_table

if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("No config file present")
    
    else:
        try:
            #Build the router from the conifg file
            config = build_table(sys.argv[1])
            router = router.Router(config)

            # Create Scheduler to run tasks
            router.scheduler = sched.scheduler(time.time, time.sleep)
            router.send_table()
            router.update_timers()
            router.print_table()
            router.scheduler.run()
        except KeyboardInterrupt:
            #Close Connections
            router.close_connections()
        