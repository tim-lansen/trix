# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from .record import *


class Interaction(Record):
    class Type:
        UNDEFINED = 0
        APPROVE = 1
        CREATE_ASSET = 2

    class Status:
        FREE = 1
        LOCK = 2
        INVALID = 3

    def __init__(self):
        super().__init__()
        self.info = None
        self.type = 0
        self.status = Interaction.Status.FREE

    TABLE_SETUP = {
        "relname": "trix_interactions",
        "fields": [
            ["info", "json NOT NULL"],
            ["type", "integer NOT NULL"],
            ["status", "integer NOT NULL"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }
