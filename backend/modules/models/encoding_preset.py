# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import uuid
from typing import List
from .record import *


class EncodingPreset(Record):

    def update_json(self, json_obj):
        super().update_json(json_obj)
        self.emitted.jobId = self.guid

    def update_str(self, json_str):
        super().update_str(json_str)
        self.emitted.jobId = self.guid

    class Parameter(JSONer):
        def __init__(self):
            super().__init__()
            self.name: str = None
            self.no_value = False
            self.value: str = None
            self.value_default = None
            # self.value_mandatory = True

    def __init__(self, name):
        super().__init__(name)
        self.encoder = None
        self.parameters: List[self.Parameter] = []

    # Table description
    TABLE_SETUP = {
        "relname": "trix_encoding_presets",
        "fields": [
            ["encoder", "name NOT NULL"],
            ["parameters", "json[] NOT NULL"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }

