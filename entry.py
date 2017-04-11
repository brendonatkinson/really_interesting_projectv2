# COSC364 Assignment 1
# Brendon Atkinson & Callum Sinclair
# 11 April 2016

class Entry(object):

    def __init__(self, update):
        self.destination = update[0]
        self.address = update[1]
        self.metric = update[2]
        self.next_hop = update[3]
        self.timeout = 180
        self.garbage = None
        self.change_flag = False

    def reset_timeout(self):
        self.timeout = 180

    def expired(self):
        self.metric = 16
        self.garbage = 120
        self.change_flag = True