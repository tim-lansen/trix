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

    class Hardware(JSONer):
        class Disk(JSONer):
            def __init__(self):
                super().__init__()
                # Path to temporary dir
                self.temp = None
                # Disk size in Gigabytes
                self.size = None
                # Disk free space in Gigabytes
                self.free = None

        def __init__(self):
            super().__init__()
            self.cpu = None
            self.memory = None
            self.disks: List[self.Disk] = []

    def __init__(self):
        super().__init__()
        self.job = None
        self.status = Node.Status.IDLE
        self.channel = None
        self.progress = None
        self.hardware = Node.Hardware()
