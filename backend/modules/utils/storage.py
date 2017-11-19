# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import os
import copy
import uuid
from random import randint
from modules.utils.log_console import Logger
from modules.config.trix_config import TrixConfig, TRIX_CONFIG


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
        pn = 0
        for server in TRIX_CONFIG.storage.servers:
            paths.append(server.get_paths(role))
            pn += len(paths[-1])
        if pn > 0:
            pn = randint(0, pn - 1)
            i = 0
            while pn >= len(paths[i]):
                pn -= len(paths[i])
                i += 1
            path: TrixConfig.Storage.Server.Path = TrixConfig.Storage.Server.Path(path=paths[i][pn], server=TRIX_CONFIG.storage.servers[i])
            if guid:
                path.sub_path += os.path.sep + guid
                if path.abs_path:
                    path.abs_path += os.path.sep + guid
                if path.web_path:
                    path.web_path += '/' + guid
        else:
            path = None #Storage.DEVNULL
        return path


def test_storage():
    Logger.log('{}\n'.format(Storage.storage_path('archive', str(uuid.uuid4()))))
    Logger.info('{}\n'.format(TRIX_CONFIG.storage.servers[0].dumps(indent=4)))
