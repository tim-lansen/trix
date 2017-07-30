# -*- coding: utf-8 -*-
# tim.lansen@gmail.com
# The Interaction record describes an interaction between backend and operator
# Operator should compose an asset from supplied media files (in future he'll be able to add media files in interface)

from typing import List
from .record import *
from .asset import Asset
from .mediafile import MediaFile


class Interaction(Record):
    class Status:
        FREE = 1
        LOCK = 2
        INVALID = 3

    class DataIn(JSONer):
        def __init__(self):
            super().__init__()
            self.asset = Asset()
            self.mediaFiles: List[MediaFile] = []

    class DataOut(JSONer):
        def __init__(self):
            super().__init__()
            self.asset = Asset()
            self.mediaFiles: List[MediaFile] = []

    def __init__(self):
        super().__init__()
        self.status = Interaction.Status.FREE
        self.dataIn = Interaction.DataIn()
        self.dataOut = Interaction.DataOut()
        self.priority = 0

    TABLE_SETUP = {
        "relname": "trix_interactions",
        "fields": [
            ["status", "integer NOT NULL"],
            ["dataIn", "json NOT NULL"],
            ["dataOut", "json"],
            ["priority", "integer"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }
