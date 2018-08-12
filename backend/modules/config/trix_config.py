# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import os
import sys
import json
from typing import List
from modules.models import *
from modules.utils.log_console import Logger, tracer
from modules.utils.jsoner import JSONer
import pprint


def config_table_using_class(C, dBase):

    def _store_class_(_C_, _where_):
        for _PC_ in reversed(_C_.__mro__):
            if 'TABLE_SETUP' in _PC_.__dict__:
                if _PC_ is _C_:
                    for k in _PC_.TABLE_SETUP:
                        v = _PC_.TABLE_SETUP[k]
                        if type(v) is str:
                            _where_[k] = v
                        elif type(v) is list:
                            if k not in _where_:
                                _where_[k] = []
                            _where_[k] += v
                        else:
                            Logger.critical('Bad TABLE_SETUP in class {}\n'.format(_C_.__name__))
                            exit(1)
                else:
                    # It's a parent class
                    if 'templates' not in _where_:
                        _where_['templates'] = []
                    _where_['templates'].append(_PC_.__name__)
                    if _PC_.__name__ not in dBase['templates']:
                        dBase['templates'][_PC_.__name__] = {}
                        _store_class_(_PC_, dBase['templates'][_PC_.__name__])

    # dBase is a config object defined in trix_config
    # It should have 'tables' and 'templates' dicts
    dBase['tables'][C.__name__] = {}
    _store_class_(C, dBase['tables'][C.__name__])


class TrixConfig(JSONer):
    class DBase(JSONer):
        class Connection(JSONer):
            def __init__(self):
                super().__init__()
                self.host = None
                self.port = None
                self.dbname = None

        def __init__(self):
            super().__init__()
            self.connection = self.Connection()
            self.users = None
            self.tables = None
            self.templates = None

        def fields(self, table_name):
            return [_[0] for _ in self.tables[table_name]['fields']]

        def conform_tables(self):
            _g_ = globals()
            # Update tables that use template
            if type(self.tables) is dict:
                for table_name in self.tables:
                    if table_name in _g_ and 'TABLE_SETUP' in _g_[table_name].__dict__:
                        Logger.debug('Using table {} definition from class\n'.format(table_name), Logger.LogLevel.LOG_INFO)
                        self.tables[table_name] = {}
                        config_table_using_class(_g_[table_name], self.__dict__)
                    table = self.tables[table_name]
                    try:
                        for template_name in table['templates']:
                            template = self.templates[template_name]
                            for key in template:
                                val = template[key]
                                if key not in table:
                                    table[key] = val
                                else:
                                    if type(val) is list:
                                        table[key] = val + table[key]
                                    else:
                                        Logger.debug("Table template value type {} not supported\n".format(type(val)), Logger.LogLevel.LOG_ERR)
                        # table.pop('templates')
                    except Exception as e:
                        Logger.error("Table {} template error\n{}\n".format(table_name, e), Logger.LogLevel.LOG_WARNING)

    class ApiServer(JSONer):
        def __init__(self):
            super().__init__()
            self.host = None
            self.port = None

    class Machines(JSONer):
        def __init__(self):
            super().__init__()
            self.comment = None
            self.default = None

    class Nodes(JSONer):

        class Role:
            INFO                            = Node.Abilities.COMBINED_INFO
            AUDIO_ENCODER                   = Node.Abilities.FFMPEG
            AUDIO_BENDER_ENCODER            = Node.Abilities.FFMPEG | Node.Abilities.SOX
            VIDEO_SLICER                    = Node.Abilities.FFMPEG | Node.Abilities.TRIM
            VIDEO_ENCODER                   = Node.Abilities.FFMPEG | Node.Abilities.X26X
            VIDEO_ENCODER_NVENC_H264        = Node.Abilities.FFMPEG | Node.Abilities.FFMPEG_NVENC_H264
            VIDEO_ENCODER_NVENC_HEVC        = Node.Abilities.FFMPEG | Node.Abilities.FFMPEG_NVENC_HEVC
            VIDEO_ENCODER_NVENC             = Node.Abilities.FFMPEG | Node.Abilities.FFMPEG_NVENC_H264 | Node.Abilities.FFMPEG_NVENC_HEVC
            VIDEO_ENCODER_SLICED            = VIDEO_SLICER | Node.Abilities.X26X
            VIDEO_ENCODER_SLICED_NVENC_H264 = VIDEO_SLICER | Node.Abilities.FFMPEG_NVENC_H264
            VIDEO_ENCODER_SLICED_NVENC_HEVC = VIDEO_SLICER | Node.Abilities.FFMPEG_NVENC_HEVC
            VIDEO_ENCODER_SLICED_NVENC      = VIDEO_SLICER | Node.Abilities.FFMPEG_NVENC_H264 | Node.Abilities.FFMPEG_NVENC_HEVC
            VIDEO_ENCODER_FULL              = VIDEO_SLICER | VIDEO_ENCODER_SLICED_NVENC | Node.Abilities.X26X

            AV_ENCODER          = AUDIO_ENCODER | VIDEO_ENCODER
            AV_BENDER_ENCODER   = AUDIO_BENDER_ENCODER | VIDEO_ENCODER
            # AV_ENCODER_SLICED = AUDIO_ENCODER | VIDEO_ENCODER_SLICED
            CONCATENATOR = Node.Abilities.FFMPEG | Node.Abilities.MP4BOX | Node.Abilities.CACHE
            COMPILER = Node.Abilities.FFMPEG | Node.Abilities.MP4BOX

        def __init__(self):
            super().__init__()
            # List of roles suggested for nodes
            self.roles: List[int] = []

        def update_str(self, json_str):
            j = json.loads(json_str)
            self.update_json(j)

        def update_json(self, json_obj):
            d = TrixConfig.Nodes.Role.__dict__
            err = False
            if 'roles' in json_obj:
                if type(json_obj['roles']) is list:
                    for v in json_obj['roles']:
                        if type(v) is str:
                            if v in d:
                                v = d[v]
                            else:
                                Logger.error('Unknown role {}\n'.format(v))
                                err = True
                                continue
                        elif type(v) is not int:
                            Logger.error('Role: bad value type {} ({})\n'.format(v, type(v)))
                            err = True
                            continue
                        self.roles.append(v)
            if err:
                Logger.critical('Exiting due to critical error(s)\n')
                exit(1)

    class Storage(JSONer):
        class Server(JSONer):
            class Path(JSONer):
                class Role:
                    UNDEFINED = 0
                    CRUDE = 1
                    CACHE = 2
                    TRANSIT = 3
                    ARCHIVE = 4
                    PRODUCTION = 5
                    PREVIEW = 6
                    WATCH = 7

                RoleMap = None

                def __init__(self, path=None, role=Role.UNDEFINED, share=None, sub_path=None, web_path=None, server=None):
                    super().__init__()
                    self.role: self.Role = role
                    self.share = share
                    # subdirectory
                    self.sub_path = sub_path
                    # WEB access path
                    self.web_path = web_path
                    # local access path
                    self.abs_path = None
                    self.mount_point = None
                    if path is not None:
                        if type(path) is dict:
                            self.update_json(path)
                        else:
                            self.role = path.role
                            self.share = path.share
                            self.sub_path = path.sub_path
                            self.web_path = path.web_path
                            self.abs_path = path.abs_path
                    if self.share is not None and self.sub_path is not None and server is not None:
                        self.mount_point = server.mount_point(self.share)
                        self.abs_path = os.path.sep.join([self.mount_point, self.sub_path])

            def __init__(self):
                super().__init__()
                self.name = None
                self.ip = None
                self.hostname = None
                self.filesystem = None
                # Typical 'share' element example:
                # "store": "/mount/disk/storage"
                self.shares = {}
                self.paths: List[self.Path] = []
                self.username = None
                self.password = None

            def network_address(self, share):
                # Compose network address of share
                # share is a name of shared resource
                if share in self.shares:
                    if self.filesystem == 'cifs':
                        # example: //TLANSEN/web
                        return '//{}/{}'.format(self.ip, share)
                    elif self.filesystem == 'nfs' or self.filesystem == 'sshfs':
                        # example: TLANSEN:/mnt/data/shared
                        return '{}:{}'.format(self.ip, self.shares[share])
                return None

            def mount_point(self, subdir=None):
                # # On Windows we use network address
                # if os.name == 'nt':
                #     return r'\\{}\{}'.format(self.hostname, subdir)
                if subdir is None:
                    return '/mnt/{}'.format(self.hostname)
                return '/mnt/{}/{}'.format(self.hostname, subdir)

            def share_local_path(self, share):
                return self.shares[share]

            def update_json(self, json_obj):
                super().update_json(json_obj)
                for i, p in enumerate(self.paths):
                    path = self.Path(path=p, server=self)
                    path.unmentioned = self.paths[i].unmentioned
                    self.paths[i] = path

            def mount_command(self, net_path, mount_point):
                if self.filesystem == 'cifs':
                    return {
                        'command': 'mount.cifs {np} {mp} -o username={u},password={p},dir_mode=0777,file_mode=0777'.format(
                            np=net_path,
                            mp=mount_point,
                            u=self.username,
                            p=self.password
                        ).split(' '),
                        'need_root': True
                    }
                elif self.filesystem == 'nfs':
                    return {
                        'command': 'mount {np} {mp} -t nfs'.format(np=net_path, mp=mount_point).split(' '),
                        'need_root': True
                    }
                elif self.filesystem == 'sshfs':
                    return {
                        'command': 'sshfs -o allow_other,reconnect,sshfs_sync,cache=no,password_stdin,big_writes {np} {mp}'.format(np=net_path, mp=mount_point).split(' '),
                        'need_root': False,
                        'stdin_pass': True
                    }
                return None

            def get_paths(self, role):
                return [_ for _ in self.paths if _.role == role]

        class Watchfolder(JSONer):
            class Action:
                UNDEFINED = 0
                INGEST = 1

            class Map(JSONer):
                def __init__(self):
                    super().__init__()
                    self.downl = 'download'
                    self.watch = 'watch'
                    self.work = 'work'
                    self.done = 'done'
                    self.fail = 'fail'

            def __init__(self):
                super().__init__()
                self.action: self.Action = self.Action.UNDEFINED
                self.path = None
                self.map: self.Map = self.Map()

            # def paths(self):
            #     return {
            #         'downl': os.path.join(self.path, self.map.downl),
            #         'watch': os.path.join(self.path, self.map.watch),
            #         'work': os.path.join(self.path, self.map.work),
            #         'done': os.path.join(self.path, self.map.done),
            #         'fail': os.path.join(self.path, self.map.fail),
            #     }

            def accessible(self):
                if os.path.isdir(self.path):
                    return {'watch': self.path}
                # paths = self.paths()
                # for p in paths:
                #     if not os.path.isdir(paths[p]):
                #         return None
                # return paths

        def __init__(self):
            super().__init__()
            self.servers_map = {}
            self.servers: List[self.Server] = []
            self.watchfolders: List[self.Watchfolder] = []

        def _remap_(self):
            self.servers_map = {}
            self.watchfolders = []
            for i, s in enumerate(self.servers):
                self.servers_map[s.hostname] = i
                for path in s.paths:
                    if path.role == path.Role.WATCH:
                        wf: TrixConfig.Storage.Watchfolder = TrixConfig.Storage.Watchfolder()
                        wf.update_json({
                            'path': path.abs_path,
                            'action': path.unmentioned['action']
                        })
                        self.watchfolders.append(wf)

        def update_str(self, json_str):
            super().update_str(json_str)
            self._remap_()

        def update_json(self, json_obj):
            super().update_json(json_obj)
            self._remap_()

        def get_server(self, server_id):
            try:
                return self.servers[self.servers_map[server_id]]
            except:
                return None

    def __init__(self):
        super().__init__()
        self.dBase = self.DBase()
        self.apiServer = self.ApiServer()
        self.nodes = self.Nodes()
        self.storage = self.Storage()


if 'TRIX_CONFIG' not in globals():
    TRIX_CONFIG = TrixConfig()
    # Read trix_config.json
    with open(os.path.join(os.path.dirname(__file__), 'trix_config.json'), 'r') as config_file:
        config_string = config_file.read()
        TRIX_CONFIG.update_str(config_string)
        TRIX_CONFIG.dBase.conform_tables()


# Check that tables config equals class definitions
def check_config_conformity():

    def str_to_class(s):
        if s in globals():
            gc = globals()[s]
            if isinstance(gc, type(object)):
                return gc
        return None

    failed = False
    for t in TRIX_CONFIG.dBase.tables:
        c = str_to_class(t)
        if c is None:
            Logger.error('No python model found for table {}\n'.format(t), Logger.LogLevel.LOG_WARNING)
            continue
        ct = TRIX_CONFIG.dBase.tables[t]
        cfields = {f[0] for f in ct['fields']}
        pfields = c().get_members_set()
        diff = cfields.symmetric_difference(pfields)
        if len(diff):
            Logger.error('{table}: config and code not conformed, check these members/fields:\n{fields}\n'.format(table=t, fields=' '.join(diff)))
            failed = True
    if failed:
        Logger.critical('check_config_conformity failed, exiting\n')
        sys.exit(1)
    Logger.debug('check_config_conformity passed\n', Logger.LogLevel.LOG_INFO)


check_config_conformity()


if TrixConfig.Storage.Server.Path.RoleMap is None:
    TrixConfig.Storage.Server.Path.RoleMap = {str(_).lower(): TrixConfig.Storage.Server.Path.Role.__dict__[_] for _ in TrixConfig.Storage.Server.Path.Role.__dict__}


if __name__ == '__main__':
    import pprint
    pprint.pprint(TRIX_CONFIG.dBase.__dict__)
    print(TRIX_CONFIG.dBase.fields('Asset'))
    print(TRIX_CONFIG.dBase.fields('MediaFile'))
    print(TRIX_CONFIG.dBase.fields('Job'))
    print(TRIX_CONFIG.dBase.fields('Machine'))
    print(TRIX_CONFIG.dBase.fields('Interaction'))
