# COSC364 Assignment 1
# Brendon Atkinson & Callum Sinclair
# 23 March 2017

import router
import sys
import sched
import time
from parse import build_table

if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("No config file present")
    
    else:

        # Build the router from the conifg file
        config = build_table(sys.argv[1])
        currRouter = router.Router(config)

        try:

            # Create Scheduler to run tasks
            currRouter.scheduler = sched.scheduler(time.time, time.sleep)
            currRouter.read_inputs()
            currRouter.send_table()
            currRouter.update_timers()
            currRouter.print_table()
            currRouter.scheduler.run()
        except KeyboardInterrupt:
            # Close Connections
            currRouter.close_connections()
