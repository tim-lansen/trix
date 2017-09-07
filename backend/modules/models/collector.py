# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import uuid
from typing import List
from .record import *


class Collector(Record):

    def __init__(self):
        super().__init__()
        # List of Job.Emitted objects
        self.results = []

    # Table description
    TABLE_SETUP = {
        "relname": "trix_collector",
        # Collector record aggregates results from jobs
        "fields": [
            ["results", "json[]"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }

