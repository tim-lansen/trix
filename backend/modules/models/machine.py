# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from typing import List
from .record import *


class Machine(Record):
    class Status:
        OFFLINE = 1
        ONLINE = 2
        INVALID = 3

    class Hardware(JSONer):
        class Disk(JSONer):
            def __init__(self):
                super().__init__()
                # Path to temporary dir
                self.temp = None
                # Disk size in Gigabytes
                self.size = None
                # Disk free space in Gigabytes
                self.free = None

        def __init__(self):
            super().__init__()
            self.cpu = None
            self.memory = None
            self.disks: List[self.Disk] = []

    def __init__(self):
        super().__init__()
        self.ip = None
        self.node_count = None
        self.node_job_types = None
        self.status = Machine.Status.OFFLINE
        self.hardware = Machine.Hardware()
        self.tmp = None

    TABLE_SETUP = {
        "comment": "machine info: hardware, ip, ",
        "relname": "trix_machines",
        "fields": [
            ["ip", "cidr NOT NULL"],
            ["node_count", "integer NOT NULL"],
            ["node_job_types", "json NOT NULL"],
            ["status", "integer NOT NULL"],
            ["hardware", "json"],
            ["tmp", "varchar(255)"]
        ],
        "fields_extra": [
            ["CONSTRAINT machine_ip_is_unique UNIQUE", "ip"],
            ["CONSTRAINT machine_name_is_unique UNIQUE", "name"]
        ],
        "creation": [
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }