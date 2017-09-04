# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Chain execution

import time
from subprocess import Popen, PIPE
from modules.models.job import Job
from modules.models.mediafile import MediaFile
from .log_console import Logger, tracer
from .combined_info import combined_info, combined_info_mediafile


def create_slices(mf: MediaFile, number_of_slices=48, min_slice_duration=30, overlap_time=15, start_frame=5, pattern_length=8):
    vt = mf.videoTracks[0]
    duration = vt.duration
    if duration/float(number_of_slices) < min_slice_duration:
        number_of_slices = int(duration / min_slice_duration)
    Logger.log('Creating slices\nSource: {}\nDUration: {}\n Count: {}\n'.format(mf.source.path, duration, number_of_slices))
    dur = duration/float(number_of_slices) + overlap_time
    slices = []
    for i in range(number_of_slices):
        draft_time = (duration * float(i) / float(number_of_slices))
        Logger.log('  creating slice at time: {0}'.format(draft_time))
        command1 = 'ffmpeg -y -loglevel quiet -ss {:.3f} -i {} -vsync 0 -map v:0 -t {:.2f} -c:v rawvideo -f rawvideo -'.format(draft_time, mf.source.path, dur)
        command2 = 'trim scan --size {} {} --pix_fmt {} --start_frame {} --pattern_length {}'.format(vt.width, vt.height, vt.pix_fmt, start_frame, pattern_length)
        proc1 = Popen(command1, stdout=PIPE, stderr=PIPE)
        proc2 = Popen(command2, stdin=proc1.stdout, stderr=PIPE)
        proc1.stderr.close()
        proc1.stdout.close()
        while proc2.poll() is None:
            time.sleep(1)
        trout = proc2.stderr.read()
        Logger.info(trout)
        if draft_time + overlap_time + dur > duration:
            dur = duration - draft_time - overlap_time
        slices.append({'time': draft_time})
    return slices
