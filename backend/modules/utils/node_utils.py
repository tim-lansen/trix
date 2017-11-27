# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import os
import platform
from subprocess import Popen
from modules.models.node import Node
from modules.config.trix_config import TrixConfig, TRIX_CONFIG


def node_abilities():
    abilities_mask = 0
    # Find out if this host is in config and supposed to have shared cache
    hostname = platform.node()
    for server in TRIX_CONFIG.storage.servers:
        if server.hostname == hostname:
            for path in server.paths:
                if path.role == TrixConfig.Storage.Server.Path.Role.CACHE:
                    abilities_mask |= Node.Abilities.CACHE
    for cb in Node.Abilities.checklist:
        success = True
        for check in Node.Abilities.checklist[cb]:
            with open(os.devnull, 'w') as nul:
                proc = Popen(check[0].split(' '), stderr=nul, stdout=nul)
                proc.communicate()
                if proc.returncode != check[1]:
                    success = False
                    break
        if success:
            abilities_mask |= cb
    return abilities_mask


def node_abilities_to_set(abilities):
    result = set([])
    for N in Node.Abilities.__dict__:
        NV = Node.Abilities.__dict__[N]
        if type(NV) is not int:
            continue
        if NV in Node.Abilities.checklist and abilities & NV != 0:
            result.add(N)
    return result
