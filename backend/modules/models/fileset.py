# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from typing import List
from .record import *


class Fileset(Record):
    class Status:
        UNDEFINED = 0
        NEW = 1
        INWORK = 2
        DONE = 3
        FAILED = 4

    class File(JSONer):
        def __init__(self):
            super().__init__()
            self.name = None
            self.ctime = None
            self.mtime = None

    def __init__(self):
        super().__init__()
        self.status = self.Status.UNDEFINED
        self.server_path = None
        self.files: List[self.File] = []
        self.dirs: List[str] = []
        self.creation_time = 0
        self.modification_time = 0

    TABLE_SETUP = {
        "relname": "trix_filesets",
        "fields": [
            ["status", "integer NOT NULL"],
            ["server_path", "text"],
            ["files", "json[]"],
            ["dirs", "text[]"],
            ["creation_time", "integer NOT NULL"],
            ["modification_time", "integer NOT NULL"]
        ],
        "creation": [
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }
