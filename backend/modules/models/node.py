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

    TABLE_SETUP = {
        "relname": "trix_nodes",
        "fields": [
            ["status", "integer NOT NULL"],
            ["channel", "name NOT NULL"],
            ["job_types", "integer[]"],
            ["job", "uuid"],
            ["progress", "double precision"]
        ],
        "fields_extra": [
            ["CONSTRAINT node_name_is_unique UNIQUE", "name"]
        ],
        "creation": [
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }
