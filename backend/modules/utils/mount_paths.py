# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import os
import re
from subprocess import call, Popen, PIPE
from modules.config.trix_config import TrixConfig, TRIX_CONFIG
from modules.utils.log_console import Logger


def mount_share(server: TRIX_CONFIG.Storage.Server, share: str, mounts):

    if mounts is None:
        parse = re.compile(r'^(.+?)\s+on\s+(.+?)\s', re.M)
        proc = Popen("mount", stdout=PIPE, stderr=PIPE)
        res = proc.communicate()
        mounts = dict(parse.findall(res[0].decode()))

    def _wrap_call_(command=None, need_root=True, error=None):
        if need_root:
            command = ['sudo', '-S'] + command
            _proc_ = Popen(command, stdin=PIPE)
            _proc_.communicate(input=b'1604001\n')
            _res_ = _proc_.returncode
        else:
            _res_ = call(command)
        if _res_ != 0:
            Logger.error(error if error else 'Error {}: {}\n'.format(_res_, ' '.join(error)))
            exit(_res_)

    np = server.network_address(share)
    desired_mp = server.local_address(share)
    if np in mounts:
        # Mount point must match desired pattern
        if desired_mp == mounts[np]:
            Logger.log('{} is already mounted to {}\n'.format(np, mounts[np]))
            return
        Logger.warning('{} is mounted to {} (must be {})\n'.format(np, mounts[np], desired_mp))
        _wrap_call_(command=['umount', mounts[np]], error='Failed to unmount {}\n'.format(mounts[np]))
        _wrap_call_(command=['rmdir', mounts[np]], error='Failed to remove {}\n'.format(mounts[np]))
    _wrap_call_(command=['mkdir', '-p', desired_mp])
    _wrap_call_(command=['chmod', '777', desired_mp])
    Logger.info('Mounting {} to {}\n'.format(np, desired_mp))
    _wrap_call_(**server.mount_command(np, desired_mp))


def mount_paths(roles: set = None):
    if os.name == 'nt':
        return True
    parse = re.compile(r'^(.+?)\s+on\s+(.+?)\s', re.M)
    proc = Popen("mount", stdout=PIPE, stderr=PIPE)
    res = proc.communicate()
    mounts = dict(parse.findall(res[0].decode()))

    def _make_dirs_(_d, _pin=False):
        if not os.path.isdir(_d):
            Logger.info('Creating directory {}\n'.format(_d))
            os.makedirs(_d)
            # Pin the folder to prevent it's deletion
            if _pin:
                with open(os.path.join(_d, '.pin'), 'w') as _f:
                    _f.write('.pin')

    dr = set([])
    if roles:
        for r in roles:
            if type(r) is str:
                if r.upper() in TrixConfig.Storage.Server.Path.Role.__dict__:
                    r = TrixConfig.Storage.Server.Path.Role.__dict__[r.upper()]
                    dr.add(r)
                else:
                    Logger.error('Cannot find any path with role "{}"\n'.format(r))
            elif type(r) is int:
                dr.add(r)
            else:
                Logger.error('Role has unsoupported type: "{}" ({})\n'.format(r, type(r)))
    dirs_to_create = []
    shares_to_mount = {}
    for server in TRIX_CONFIG.storage.servers:
        for path in server.paths:
            # Logger.warning('{}\n'.format(path.dumps()))
            if roles is None or path.role in dr:
                dirs_to_create.append(path.abs_path)
                sid = '{}:{}'.format(server.hostname, path.share)
                shares_to_mount[sid] = [server, path.share]
                Logger.error('{}\n'.format(path.abs_path))

    for sid in shares_to_mount:
        server, share = shares_to_mount[sid]
        mount_share(server, share, mounts)

    for dtc in dirs_to_create:
        _make_dirs_(dtc)

    # try:
    #     for wf in TRIX_CONFIG.storage.watchfolders:
    #         Logger.log('{}\n'.format(wf.dumps(indent=2)))
    #         _make_dirs_(os.path.join(wf.path, wf.map.downl), _pin=True)
    #         _make_dirs_(os.path.join(wf.path, wf.map.watch), _pin=True)
    #         _make_dirs_(os.path.join(wf.path, wf.map.work), _pin=True)
    #         _make_dirs_(os.path.join(wf.path, wf.map.done), _pin=True)
    #         _make_dirs_(os.path.join(wf.path, wf.map.fail), _pin=True)
    # except Exception as e:
    #     Logger.error('{}\n'.format(e))
    #     return False

    return True


def test_mount_paths(roles: set = None):
    if mount_paths(roles):
        Logger.log('Passed\n')
    else:
        Logger.log('Not passed\n')
