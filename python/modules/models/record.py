# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from modules.utils.jsoner import JSONer


# The DB record template
class Record(JSONer):
    def __init__(self):
        super().__init__()
        self.id = None
        self.name = None
        self.ctime = None
        self.mtime = None


def test():
    rec = Record()
    rec.update_str('{"id": "a53b316b-461f-4662-8168-8d849bb4060d", "name": "test"}')
    print(rec.dumps(indent=2))
