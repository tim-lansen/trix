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


def mp4box_concat(output: str, params: str, video_segments: List[str], audio_tracks: List[str]):
    if len(audio_tracks) == 0:
        command = 'MP4Box {params}-out {out} -tmp {temp} -new /dev/null {video}'.format(
            params='{} '.format(params) if len(params) else '',
            out=output,
            temp='/tmp/',
            video=' '.join(['-cat {}'.format(_) for _ in video_segments])
        )
        Logger.debug('{}\n'.format(command), Logger.LogLevel.LOG_ERR)
        proc = Popen(command.split(' '), stdin=sys.stdin, stderr=PIPE)
        # pipe_nowait(proc.stderr)
        stde = proc.stderr.fileno()

        while proc.poll() is None:
            line = proc.stderr.read().decode().replace('\r', '')
            Logger.log('{}\n'.format(line))
        Logger.info('Result: {}\n'.format(proc.returncode))
    else:
        vtmp = '{}/__tmp__.mp4'.format(os.path.dirname(video_segments[0]))
        command = 'MP4Box {params}-out {out} -tmp {temp} -new /dev/null {video}'.format(
            params='{} '.format(params) if len(params) else '',
            out=vtmp,
            temp='/tmp/',
            video=' '.join(['-cat {}'.format(_) for _ in video_segments])
        )
        Logger.debug('{}\n'.format(command), Logger.LogLevel.LOG_ERR)
        proc = Popen(command.split(' '), stdin=sys.stdin, stderr=PIPE)
        # pipe_nowait(proc.stderr)
        stde = proc.stderr.fileno()

        while proc.poll() is None:
            line = proc.stderr.read().decode().replace('\r', '')
            Logger.log('{}\n'.format(line))
        Logger.info('Result: {}\n'.format(proc.returncode))

        command = 'MP4Box {params}-out {out} -tmp {temp} -new /dev/null -add {video} {audio}'.format(
            params='{} '.format(params) if len(params) else '',
            out=output,
            temp='/tmp/',
            video=vtmp,
            audio=' '.join(['-add {}'.format(_) for _ in audio_tracks])
        )
        command = 'ffmpeg -loglevel error -stats -i {video} {audio} -c copy {out}'.format(
            out=output,
            video=vtmp,
            audio=' '.join(['-i {}'.format(_) for _ in audio_tracks])
        )
        Logger.debug('{}\n'.format(command), Logger.LogLevel.LOG_ERR)
        proc = Popen(command.split(' '), stdin=sys.stdin, stderr=PIPE)
        pipe_nowait(proc.stderr)
        stde = proc.stderr.fileno()

        while proc.poll() is None:
            # line = proc.stderr.read().decode().replace('\r', '')
            try:
                line = os.read(stde, 65536)
                Logger.log('{}\n'.format(line))
            except:
                pass
        Logger.info('Result: {}\n'.format(proc.returncode))

        os.remove(vtmp)

    return proc.returncode


