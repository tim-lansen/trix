# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import os
from random import randint
from modules.config import TRIX_CONFIG


class Storage:

    if os.name == 'nt':
        DEVNULL = 'nul'
    else:
        DEVNULL = '/dev/null'

    @staticmethod
    def storage_path(role, guid):
        # TODO: decision must base on storage load, source location, etc...
        paths = []
        for server in TRIX_CONFIG.storage.servers:
            paths += server.get_paths(role)
        if len(paths):
            path = '{}{}{}'.format(paths[randint(0, len(paths) - 1)], os.path.sep, guid)
        else:
            path = Storage.DEVNULL
        return path

