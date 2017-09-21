# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import os
import re
from subprocess import call, Popen, PIPE
from modules.config import *
from modules.utils.log_console import Logger


def mount_paths():
    if os.name == 'nt':
        return True
    parse = re.compile(r'^(.+?)\s+on\s+(.+?)\s', re.M)
    proc = Popen("mount", stdout=PIPE, stderr=PIPE)
    res = proc.communicate()
    mount = dict(parse.findall(res[0].decode()))

    def _wrap_call_(_params_, _su_=True, _error_=None):
        if _su_:
            _params_ = ['sudo', '-S'] + _params_
            _proc_ = Popen(_params_, stdin=PIPE)
            _proc_.communicate(input=b'1604001\n')
            _res_ = _proc_.returncode
        else:
            _res_ = call(_params_)
        if _res_ != 0:
            Logger.error(_error_ if _error_ else 'Error {}: {}\n'.format(_res_, ' '.join(_params_)))
            exit(_res_)

    def _make_dirs_(_d, _pin=False):
        if not os.path.isdir(_d):
            Logger.info('Creating directory {}\n'.format(_d))
            os.makedirs(_d)
            # Pin the folder to prevent it's deletion
            if _pin:
                with open(os.path.join(_d, '.pin'), 'w') as _f:
                    _f.write('.pin')

    for server in TRIX_CONFIG.storage.servers:
        Logger.warning('{}\n'.format(server.dumps(indent=2)))
        for share in server.shares:
            np = server.network_address(share)
            desired_mp = server.mount_point(share)
            if np in mount:
                # Mount point must match desired pattern
                if desired_mp == mount[np]:
                    Logger.info('{} is mounted to {}\n'.format(np, mount[np]))
                    continue
                Logger.warning('{} is mounted to {} (must be {})\n'.format(np, mount[np], desired_mp))
                _wrap_call_(['umount', mount[np]], 'Failed to unmount {}\n'.format(mount[np]))
                _wrap_call_(['rmdir', mount[np]], 'Failed to remove {}\n'.format(mount[np]))
            _wrap_call_(['mkdir', '-p', desired_mp])
            _wrap_call_(['chmod', '777', desired_mp])
            _wrap_call_(['mount', np, desired_mp] + server.mount_opts())
    for server in TRIX_CONFIG.storage.servers:
        for path in server.paths:
            mp = server.mount_point(path['net_path'])
            _make_dirs_(mp)
    for wf in TRIX_CONFIG.storage.watchfolders:
        _make_dirs_(os.path.join(wf.path, wf.map.downl), _pin=True)
        _make_dirs_(os.path.join(wf.path, wf.map.watch), _pin=True)
        _make_dirs_(os.path.join(wf.path, wf.map.work), _pin=True)
        _make_dirs_(os.path.join(wf.path, wf.map.done), _pin=True)
        _make_dirs_(os.path.join(wf.path, wf.map.fail), _pin=True)

    return True


def test():
    if mount_paths():
        Logger.log('Passed\n')
    else:
        Logger.log('Not passed\n')
