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

    def __init__(self, name='', guid=0):
        super().__init__(name=name, guid=guid)
        # List of various results
        self.collected = []

    # Table description
    TABLE_SETUP = {
        "relname": "trix_collector",
        "fields": [
            ["collected", "text[]"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }

