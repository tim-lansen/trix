# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import os
import re
import platform
from subprocess import call, Popen, PIPE
from modules.config.trix_config import TrixConfig, TRIX_CONFIG
from modules.utils.log_console import Logger


def _wrap_call_(command, need_root=True, stdin_pass=False, error=None, std=None):
    # std is a dict
    # return std out/err to std['stdout'] and std['stderr']
    Logger.debug('{}\n'.format(' '.join(command)))
    if need_root:
        command = ['sudo', '-S'] + command
        _proc_ = Popen(command, stdin=PIPE)
        stds = _proc_.communicate(input=b'1604001\n')
        _res_ = _proc_.returncode
    elif stdin_pass:
        _proc_ = Popen(command, stdin=PIPE)
        stds = _proc_.communicate(input=b'1604001\n')
        _res_ = _proc_.returncode
    else:
        _proc_ = Popen(command, stderr=PIPE, stdout=PIPE)
        stds = _proc_.communicate()
        _res_ = _proc_.returncode
    if _res_ != 0:
        Logger.error(error if error else 'Error {}: {}\n'.format(_res_, ' '.join(error)))
        exit(_res_)
    if type(std) is dict:
        std['stdout'] = stds[0]
        std['stderr'] = stds[1]
    return _res_


def symlink_origin(symlink):
    proc = Popen('ls -ld "{}"'.format(symlink), stdout=PIPE, shell=True)
    s = proc.communicate()
    x = re.findall(r'^.+?(/.+) -\> (/.+)$', s[0])
    if len(x) == 1 and len(x[0]) == 2:
        return x[0][1]
    return None


def get_mounts():
    parse = re.compile(r'^(.+?)\s+on\s+(.+?)\s', re.M)
    proc = Popen("mount", stdout=PIPE, stderr=PIPE)
    res = proc.communicate()
    mounts = dict(parse.findall(res[0].decode()))
    return mounts


def mount_share(server: TRIX_CONFIG.Storage.Server, share: str):
    exit(2)
    mounts = get_mounts()

    np = server.network_address(share)
    mount_point = server.mount_point(share)
    Logger.critical('NP: {}  MP: {}\n'.format(np, mount_point))
    # if server.hostname == platform.node():
        # Locally [create and] link resources

    # Special case for cache host
    # if share == 'cache' and server.hostname == platform.node():
    #     np = 'ramfs'
    # else:

    return
    if np in mounts:
        # Mount point must match desired pattern
        if mount_point == mounts[np]:
            Logger.log('{} is already mounted to {}\n'.format(np, mounts[np]))
            return
        Logger.warning('{} is mounted to {} (must be {})\n'.format(np, mounts[np], mount_point))
        _wrap_call_(command=['umount', mounts[np]], error='Failed to unmount {}\n'.format(mounts[np]))
        _wrap_call_(command=['rmdir', mounts[np]], error='Failed to remove {}\n'.format(mounts[np]))
    _wrap_call_(command=['mkdir', '-p', mount_point])
    Logger.info('Mounting {} to {}\n'.format(np, mount_point))
    if server.hostname == platform.node():
        if share == 'cache':
            # Create RAMFS, mount it
            _wrap_call_(command=['mount', '-t', 'ramfs', 'ramfs', mount_point])
            _wrap_call_(command=['chmod', '777', mount_point])
        else:
            Logger.critical('MOUNT LOCAL: {} to {}\n'.format(mount_point, np))
    else:
        _wrap_call_(command=['chmod', '777', mount_point])
        _wrap_call_(**server.mount_command(np, mount_point))


def local_share(server: TRIX_CONFIG.Storage.Server, share: str):

    mounts = get_mounts()

    # Server local resource path
    local_path = server.share_local_path(share)
    # Shared mount point
    mount_point = server.mount_point(share)
    Logger.critical('Local: {}  Mount: {}\n'.format(local_path, mount_point))

    # On the server holding this share, mount point must be a symbolic link
    # Check symlink and unlink it if it is wrong
    if os.path.exists(mount_point):
        if os.path.islink(mount_point):
            if local_path != symlink_origin(mount_point):
                _wrap_call_(command=['unlink', mount_point])
        else:
            Logger.critical('Mount point "{mp}" on host "{host}" must be a symlink, but it is not\n'.format(mp=mount_point, host=server.hostname))
            exit(1)

    if share == 'ramcache':
        if 'ramfs' in mounts:
            if local_path == mounts['ramfs']:
                Logger.log('RAMFS is already mounted to {}\n'.format(local_path))
            else:
                Logger.warning('RAMFS is mounted to {} (must be {})\n'.format(mounts['ramfs'], local_path))
                # Release RAMFS
                _wrap_call_(command=['umount', mounts['ramfs']])
                # Mount RAMFS
                _wrap_call_(command=['mount', '-t', 'ramfs', 'ramfs', local_path])
                _wrap_call_(command=['chown', 'tim', local_path])
    else:
        # Check if local path is a directory
        if os.path.exists(local_path):
            if not os.path.isdir(local_path):
                Logger.critical('Local path "{lp}" for share "{share}" on host "{host}" must be a directory, but it is not\n'.format(
                    lp=local_path, share=share, host=server.hostname)
                )
                exit(1)
        else:
            # Try to create directory
            _wrap_call_(command=['mkdir', '-p', local_path], need_root=False)
    if not os.path.islink(mount_point):
        _wrap_call_(command=['ln', '-s', local_path, mount_point], need_root=False)


def mount_paths(roles: set = None):
    # Mount all shares and create all paths if roles is None
    if os.name == 'nt':
        return True

    def _make_dirs_(_d, _pin=False):
        if not os.path.isdir(_d):
            Logger.info('Creating directory {}\n'.format(_d))
            _wrap_call_(command=['mkdir', '-p', _d])
            _wrap_call_(command=['chown', 'tim', _d])
            _wrap_call_(command=['chmod', '777', _d], need_root=False)
            # os.makedirs(_d)
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
            Logger.warning('{}\n'.format(path.dumps()))
            if roles is None or path.role in dr:
                if server.hostname == platform.node():
                    # Local resources
                    local_share(server, path.share)
                else:
                    dirs_to_create.append(path.abs_path)
                    sid = '{}:{}'.format(server.hostname, path.share)
                    shares_to_mount[sid] = [server, path.share]
                    Logger.error('{}\n'.format(path.abs_path))

    for sid in shares_to_mount:
        server, share = shares_to_mount[sid]
        mount_share(server, share)

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
