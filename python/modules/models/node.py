# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from .record import *


class Node(Record):
    class Status:
        IDLE = 1
        BUSY = 2
        INVALID = 3

    def __init__(self):
        super().__init__()
        self.job = None
        self.status = Node.Status.IDLE
        self.channel = None
        self.progress = None
