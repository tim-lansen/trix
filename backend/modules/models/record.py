# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from modules.utils.jsoner import JSONer
from modules.utils.types import Guid


# Database record template
class Record(JSONer):
    def __init__(self, name=None, guid=None):
        super().__init__()
        self.guid = Guid(guid)
        self.name = name
        self.ctime = None
        self.mtime = None

    TABLE_SETUP = {
        "fields": [
            ["guid", "uuid NOT NULL"],
            ["name", "name NOT NULL"],
            ["ctime", "timestamp without time zone"],
            ["mtime", "timestamp without time zone"]
        ],
        "fields_extra": [
            ["PRIMARY KEY", "guid"]
        ],
        "creation": [
            "CREATE TABLE public.{relname} ({fields}) WITH (OIDS = FALSE);",
            "ALTER TABLE public.{relname} OWNER to {superuser};",
            "GRANT ALL ON TABLE public.{relname} TO trix WITH GRANT OPTION;"
        ]
    }


def test():
    rec = Record()
    rec.update_str('{"guid": "a53b316b-461f-4662-8168-8d849bb4060d", "name": "test"}')
    print(rec.dumps(indent=2))
