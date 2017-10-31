# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import uuid
from typing import List
from .record import *


class Collector(Record):
    # Collector record aggregates results from jobs

    class SliceResult(JSONer):
        def __init__(self):
            super().__init__()
            self.start = 0.0
            self.frames = 0
            self.duration = 0.0
            self.showinfo = None
            self.blackdetect = None

    class AudioResults(JSONer):
        def __init__(self):
            super().__init__()
            # Silencedetect is captured only for 1st audio track
            # This array contain records like
            # {"silence_start": 0.042, "silence_end": 30.074, "silence_duration": 30.032}
            self.silencedetect = []
            # Astats is captured for every audio track
            #
            self.astats = []

    def __init__(self, name='', guid=None):
        super().__init__(name=name, guid=guid)
        # List of various results
        self.sliceResults: List[self.SliceResult] = []
        self.audioResults: self.AudioResults = self.AudioResults()

    # Table description
    TABLE_SETUP = {
        "relname": "trix_collector",
        "fields": [
            ["sliceResults", "text[]"],
            ["audioResults", "text[]"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }

