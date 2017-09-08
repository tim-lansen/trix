# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import time
import json
from subprocess import Popen, PIPE
from modules.models.job import Job
from modules.models.mediafile import MediaFile
from .log_console import Logger, tracer
from .combined_info import combined_info, combined_info_mediafile
from .jsoner import JSONer


class Slice(JSONer):
    def __init__(self):
        super().__init__()
        self.length = 0
        self.pattern_offset = 0
        self.time = 0
        self.crc = []


def create_slices(mf: MediaFile, vti=0, number_of_slices=48, min_slice_duration=30, overlap_time=15, start_frame=5, pattern_length=8):
    pattern_search_distance = start_frame + 5 * pattern_length
    vt = mf.videoTracks[vti]
    duration = vt.duration
    if duration/float(number_of_slices) < min_slice_duration:
        number_of_slices = int(duration / min_slice_duration)
    Logger.log('Creating slices\nSource: {}\nDUration: {}\n Count: {}\n'.format(mf.source.path, duration, number_of_slices))
    dur = duration/float(number_of_slices) + overlap_time
    slices = []
    for i in range(number_of_slices):
        draft_time = int((duration * float(i) / float(number_of_slices)))
        Logger.log('  creating slice at time: {0}\n'.format(draft_time))
        command1 = 'ffmpeg -y -loglevel quiet -ss {:.3f} -i {} -vsync 1 -r {} -map v:{} -vframes {} -c:v rawvideo -f rawvideo -'.format(draft_time, mf.source.path, vt.fps, vti, pattern_search_distance)
        command2 = '/home/tim/projects/trim/bin/x64/Debug/trim.out scan --size {} {} --pix_fmt {} --start_frame {} --pattern_length {}'.format(vt.width, vt.height, vt.pix_fmt, start_frame, pattern_length)
        proc1 = Popen(command1.split(' '), stdout=PIPE, stderr=PIPE)
        proc2 = Popen(command2.split(' '), stdin=proc1.stdout, stderr=PIPE)
        proc1.stderr.close()
        proc1.stdout.close()
        while proc2.poll() is None:
            time.sleep(1)
        trout = proc2.stderr.read().decode()
        slic = {'time': draft_time}
        for line in trout.split(';'):
            kv = line.split('=', 1)
            if len(kv) == 2:
                vv = kv[1].split(',')
                if len(vv) == 1:
                    slic[kv[0]] = kv[1]
                else:
                    slic[kv[0]] = vv
        if 'crc' not in slic:
            Logger.warning('Unable to create slice at {}\n'.format(draft_time))
        else:
            Logger.info('{}\n'.format(slic))
            slices.append(slic)
        if draft_time + overlap_time + dur > duration:
            dur = duration - draft_time - overlap_time
    return slices


def test():
    from .combined_info import combined_info_mediafile
    from .ffmpeg_utils import FFMPEG_UTILS_TEST_FILE_AVS
    from pprint import pprint
    mf = combined_info_mediafile(FFMPEG_UTILS_TEST_FILE_AVS)
    slices = create_slices(mf)
    pprint(slices)