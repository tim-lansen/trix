# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from typing import List
from .record import *


class Node(Record):
    class Status:
        IDLE = 1
        BUSY = 2
        OFFER = 3
        INVALID = 4

    def __init__(self):
        super().__init__()
        self.job = None
        self.job_types = None
        self.status = Node.Status.IDLE
        self.channel = None
        self.progress = None
