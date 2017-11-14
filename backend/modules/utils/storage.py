# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import os
import copy
from random import randint
from modules.config import TRIX_CONFIG


class Storage:

    # class Location:
    #     def __init__(self):
    #         self.path = None
    #         self.url = None

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
            # path = '{}{}{}'.format(paths[randint(0, len(paths) - 1)].net_path, os.path.sep, guid)
            path = paths[randint(0, len(paths) - 1)]
            if guid:
                path.net_path += os.path.sep + guid
                if path.web_path:
                    path.web_path += '/' + guid
        else:
            path = None #Storage.DEVNULL
        return path


