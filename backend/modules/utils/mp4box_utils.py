# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import re
import os
import sys
import copy
import time
from pprint import pprint
from .parsers import Parsers, timecode_to_float
from .log_console import Logger
from subprocess import Popen, PIPE
from .pipe_nowait import pipe_nowait
from .combined_info import combined_info
from typing import List
from modules.models.mediafile import MediaFile
from modules.models.asset import Asset, Stream
from modules.utils.storage import Storage


def mp4box_concat(output: str, params: str, inputs: List[str]):
    command = 'MP4Box {params}-out {out} -tmp {temp} -new /dev/null {inputs}'.format(
        params='{} '.format(params) if len(params) else '',
        out=output,
        temp='/tmp/',
        inputs=' '.join(['-cat {}'.format(_) for _ in inputs])
    ).split(' ')
    proc = Popen(command, stdin=sys.stdin, stderr=PIPE)
    # pipe_nowait(proc.stderr)
    stde = proc.stderr.fileno()

    while proc.poll() is None:
        line = proc.stderr.read().decode().replace('\r', '')
        Logger.log('{}\n'.format(line))
    Logger.info('Result: {}\n'.format(proc.returncode))
    return proc.returncode


