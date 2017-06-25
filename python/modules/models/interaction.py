# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from .record import *


class Interaction(Record):
    class Status:
        IDLE = 1
        BUSY = 2
        INVALID = 3

    def __init__(self):
        super().__init__()
        self.info = None
        self.status = Interaction.Status.IDLE
