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

    def _wrap_call_(_params_, _error_=None):
        _res_ = call(_params_)
        if _res_ != 0:
            Logger.error(_error_ if _error_ else 'Error {}: {}\n'.format(_res_, ' '.join(_params_)))
            exit(_res_)

    for server in TRIX_CONFIG.storage.servers:
        for share in server.shares:
            netpath = '//{}/{}'.format(server.address, share)
            desired_mp = server.mount_point(share)
            if netpath in mount:
                # Mount point must match desired pattern
                if desired_mp == mount[netpath]:
                    Logger.info('{} on {}\n'.format(netpath, mount[netpath]))
                    continue
                Logger.warning('{} on {} (must be {})\n'.format(netpath, mount[netpath], desired_mp))
                # unmount.append(mount[netpath])
                _wrap_call_(['sudo', 'umount', mount[netpath]], 'Failed to unmount {}\n'.format(mount[netpath]))
                _wrap_call_(['sudo', 'rmdir', mount[netpath]], 'Failed to remove {}\n'.format(mount[netpath]))
            _wrap_call_(['sudo', 'mkdir', '-p', desired_mp])
            _wrap_call_(['sudo', 'chmod', '755', desired_mp])
            _wrap_call_(['sudo', 'mount', netpath, desired_mp] + server.mount_opts())
    return True


def test():
    if mount_paths():
        Logger.log('Passed\n')
    else:
        Logger.log('Not passed\n')
