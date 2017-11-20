# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import os
from typing import List
from .record import *


class Fileset(Record):
    class Status:
        UNDEFINED = 0
        NEW = 1
        IGNORE = 2
        INWORK = 3
        DONE = 4
        FAILED = 5

    class File(JSONer):
        def __init__(self):
            super().__init__()
            self.name = None
            self.ctime = None
            self.mtime = None
            self.size = 0

    def __init__(self, init: dict=None):
        super().__init__()
        self.status = self.Status.UNDEFINED
        self.path = None
        self.files: List[self.File] = []
        self.dirs: List[str] = []
        self.creation_time = 0
        self.modification_time = 0
        if init is not None:
            self.update_json(init)

    TABLE_SETUP = {
        "relname": "trix_filesets",
        "fields": [
            ["status", "integer NOT NULL"],
            ["path", "text"],
            ["files", "json[]"],
            ["dirs", "text[]"],
            ["creation_time", "float NOT NULL"],
            ["modification_time", "float NOT NULL"]
        ],
        "creation": [
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }

    FIELDS_FOR_UPDATE = {'files', 'dirs', 'creation_time', 'modification_time'}
    FIELDS_FOR_LIST = {'name', 'guid', 'creation_time', 'modification_time', 'status'}


    def __eq__(self, other):
        # Ignore dirs completely
        if self.name != other.name:
            print('#1.1')
            return False
        if self.path != other.path:
            print('#1.2')
            return False
        # if self.creation_time != other.creation_time:
        #     print('#1.3')
        #     return False
        if int(self.modification_time) != int(other.modification_time) or len(self.files) != len(other.files):
            print('{} != {}'.format(int(self.modification_time), int(other.modification_time)))
            return False
        sfd = {_.name: _ for _ in self.files}
        for of in other.files:
            if of.name not in sfd:
                print('#3')
                return False
            sf = sfd[of.name]
            if int(sf.ctime) != int(of.ctime) or int(sf.mtime) != int(of.mtime) or int(sf.size) != int(of.size):
                print('#4')
                return False
        return True

    @staticmethod
    def fileset(path):
        fs: Fileset = Fileset()
        fs.name = os.path.basename(path)
        stat = os.stat(path)
        fs.creation_time = stat.st_ctime
        fs.modification_time = stat.st_mtime
        for f in os.listdir(path):
            fpath = os.path.join(path, f)
            stat = os.stat(fpath)
            # fs.modification_time = max(fs.modification_time, stat.st_mtime)
            if os.path.isfile(fpath):
                file: Fileset.File = Fileset.File()
                file.name = f
                file.ctime = stat.st_ctime
                file.mtime = stat.st_mtime
                file.size = stat.st_size
                fs.files.append(file)
            elif os.path.isdir(fpath):
                fs.dirs.append(f)
        return fs

    @staticmethod
    def filesets(path):
        fss = []
        for d in os.listdir(path):
            dpath = os.path.join(path, d)
            if os.path.isdir(dpath):
                fss.append(Fileset.fileset(dpath))
        return fss
