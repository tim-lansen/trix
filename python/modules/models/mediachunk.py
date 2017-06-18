# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from modules.models.record import *


class MediaChunk(Record):
    def __init__(self):
        super().__init__()
        # ID of media file that owns this chunk
        self.ownerId = None
        # This chunk's order in sequence
        self.ownerIndex = None
        # Number of frames stored in chunk
        self.frameCount = None
