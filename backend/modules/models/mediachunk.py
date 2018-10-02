# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from modules.models.record import *


class MediaChunk(Record):

    # Guid type support class
    class OwnerId(Guid):
        def __init__(self):
            super().__init__()

    def __init__(self):
        super().__init__()
        # ID of media file that owns this chunk
        self.ownerId = Guid()
        # This chunk's order in sequence
        # self.ownerIndex = None
        # Number of frames stored in chunk
        self.frameCount = 0

    TABLE_SETUP = {
        "relname": "trix_chunks",
        "fields": [
            ["ownerId", "uuid NOT NULL"],
            ["frameCount", "integer NOT NULL"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }
