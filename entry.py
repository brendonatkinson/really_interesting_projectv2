# COSC364 Assignment 1
# Brendon Atkinson & Callum Sinclair
# 11 April 2017
import time

TIMEOUT = 180
GARBAGE = 120
RIP_INFINITY = 16

class Entry(object):

    def __init__(self, update):
        self.destination = update[0]
        self.address = update[1]
        self.metric = update[2]
        self.next_hop = update[3]
        self.timeout = time.time() + TIMEOUT
        self.garbage = GARBAGE
        self.change_flag = False
        self.expired_flag = False

    def reset_timeout(self):
        self.timeout = time.time() + TIMEOUT
        self.garbage = GARBAGE
        self.change_flag = False
        self.expired_flag = False

    def expired(self):
        self.metric = RIP_INFINITY
        self.garbage = time.time() + TIMEOUT
        self.change_flag = True
        self.expired_flag = True

    def timeout_remaining(self):
        if self.expired_flag:
            return 0.0
        else:
            return self.timeout - time.time()

    def garbage_remaining(self):
        if self.expired_flag:
            return self.garbage - time.time()
        else:
            return self.garbage
