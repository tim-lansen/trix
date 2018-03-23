# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import time
import json
from pprint import pformat, pprint
from subprocess import Popen, PIPE
from modules.models.job import Job
from modules.models.mediafile import MediaFile
from .log_console import Logger, tracer
from .combined_info import combined_info, combined_info_mediafile
from .ffmpeg_utils import DEVNULL
from .parsers import Parsers


"""
Новый способ нарезки на слайсы (ffmpeg-only)

1. Сканируем участок
ffmpeg -nostats -y -ss 200 -i E:\media\avatar.1080p.mp4 -t 230 -map v -copyts -vf "select=gte(scene\,0.3),showinfo" -f null nul
[Parsed_showinfo_1 @ 000002a0c760d1c0] n:   0 pts:2655232 pts_time:207.44  pos:109117394 fmt:rgb24 sar:1/1 s:1920x1080 i:P iskey:0 type:P checksum:F67B5321 plane_checksum:[F67B5321] mean:[39] stdev:[39.8]

ffmpeg -nostats -y -ss 220 -i E:\media\avatar.1080p.mp4 -t 230 -map v -copyts -vf "select=gte(scene\,0.3),showinfo" -f null nul
[Parsed_showinfo_1 @ 000001a6b0ed48c0] n:   0 pts:2818048 pts_time:220.16  pos:117139028 fmt:rgb24 sar:1/1 s:1920x1080 i:P iskey:0 type:P checksum:534FCDE9 plane_checksum:[534FCDE9] mean:[64] stdev:[54.5]

ffmpeg -nostats -y -ss 230 -i E:\media\avatar.1080p.mp4 -t 240 -map v -copyts -vf "select=gte(scene\,0.3),showinfo" -f null nul
[Parsed_showinfo_1 @ 0000024817d03e00] n:   0 pts:2982912 pts_time:233.04  pos:128364608 fmt:rgb24 sar:1/1 s:1920x1080 i:P iskey:0 type:P checksum:00C47242 plane_checksum:[00C47242] mean:[98] stdev:[49.3]

pts_time:207.44
pts_time:220.16
pts_time:233.04

2. Команды (грязный хак - ниже по пайпу читаем только фрагмент, т.к. первая команда будет читать файл до конца)
ffmpeg -y -ss 207 -i E:\media\avatar.1080p.mp4 -map v -vsync 1 -vf "select=gte(t\,0.44)*lt(t\,12.72)" -c:v libx264 -flags cgop -preset slow -x264opts "keyint=50:min_keyint=9:ref=2:bframes=3" T:\temp\p1.h264 -map v -f rawvideo -|ffmpeg -f rawvideo -y -loglevel error -s 1920:1080 -r 25 -pix_fmt yuv420p -i - -t 14 -f null nul

ffmpeg -y -ss 220 -i E:\media\avatar.1080p.mp4 -map v -vsync 1 -vf "select=gte(t\,0.16)*lt(t\,12.88)" -c:v libx264 -flags cgop -preset slow -x264opts "keyint=50:min_keyint=9:ref=2:bframes=3" T:\temp\p2.h264 -map v -f rawvideo -|ffmpeg -f rawvideo -y -loglevel error -s 1920:1080 -r 25 -pix_fmt yuv420p -i - -t 14 -f null nul

собираем
echo file p1.h264 >list
echo file p2.h264 >>list
ffmpeg -y -loglevel error -stats -f concat -i list -c copy pallc.mp4

проверяем
ffmpeg -y -ss 207 -i E:\media\avatar.1080p.mp4 -map v -vsync 1 -vf "select=gte(t\,0.44)*lt(t\,25.6)" -c:v libx264 -flags cgop -preset slow -x264opts "keyint=50:min_keyint=9:ref=2:bframes=3" T:\temp\pall.mp4 -map v -f rawvideo -|ffmpeg -f rawvideo -y -loglevel error -s 1920:1080 -r 25 -pix_fmt yuv420p -i - -t 26 -f null nul

ffprobe -v quiet -show_streams -count_frames pallc.mp4|find "nb_fra"
nb_frames=640

ffprobe -v quiet -show_streams -count_frames pall.mp4|find "nb_fra"
nb_frames=640


"""


def create_slices(mf: MediaFile, vti=0, number_of_slices=48, min_slice_duration=48, first_slice_duration=120, overlap_time=15, start_frame=0, pattern_length=8):
    pattern_search_distance = start_frame + 32 * pattern_length
    vt = mf.videoTracks[vti]
    duration = vt.duration
    if duration < first_slice_duration + min_slice_duration:
        return []
    if (duration - first_slice_duration)/float(number_of_slices) < min_slice_duration:
        number_of_slices = 1 + int((duration - first_slice_duration) / min_slice_duration)
    Logger.log('Creating slices\nSource: {}\nDUration: {}\n Count: {}\n'.format(mf.source.path, duration, number_of_slices))

    dur0 = first_slice_duration
    dur1 = (duration - first_slice_duration)/float(number_of_slices)

    timebase = None
    slices = []
    for i in range(number_of_slices):
        if i == 0:
            dur = dur0 + overlap_time
            draft_time = 0.0
        else:
            dur = dur1 + overlap_time
            draft_time = first_slice_duration + dur1 * float(i)
        Logger.log('  creating slice at time: {0}\n'.format(draft_time))
        command1 = 'ffmpeg -y -loglevel quiet -ss {:.3f} -i {} -vsync 1 -r {} -map v:{} -vframes {} -c:v rawvideo -f rawvideo -'.format(draft_time, mf.source.path, vt.fps, vti, pattern_search_distance)
        command2 = 'trim.out scan --size {} {} --pix_fmt {} --start_frame {} --pattern_length {}'.format(vt.width, vt.height, vt.pix_fmt, start_frame, pattern_length)
        proc1 = Popen(command1.split(' '), stdout=PIPE, stderr=PIPE)
        proc2 = Popen(command2.split(' '), stdin=proc1.stdout, stderr=PIPE)
        proc1.stderr.close()
        proc1.stdout.close()
        while proc2.poll() is None:
            time.sleep(0.1)
        trout = proc2.stderr.read().decode()
        slic = {'time': draft_time}
        for line in trout.split(';'):
            kv = line.strip().split('=', 1)
            if len(kv) == 2:
                vv = kv[1].split(',')
                if len(vv) == 1:
                    slic[kv[0]] = int(kv[1])
                else:
                    slic[kv[0]] = [int(_) for _ in vv]
        if 'crc' in slic:
            command = 'ffmpeg -y -ss {start:.3f} -i {input} -copyts -r {fps} -vf showinfo -map v:{vti} -vframes {frames} -c:v rawvideo -f null {devnull}'.format(
                start=draft_time,
                input=mf.source.path,
                fps=vt.fps,
                vti=vti,
                frames=2 + slic['pattern_offset'],
                devnull=DEVNULL
            )
            proc = Popen(command.split(' '), stdout=PIPE, stderr=PIPE)
            while proc.poll() is None:
                time.sleep(0.1)
            output = proc.stderr.read().decode()
            parsed = Parsers.ffmpeg_auto_text(output)
            # Search pattern start frame
            Logger.warning('{}\n'.format(slic))
            for frame in parsed['showinfo'][0]:
                if timebase is None and 'config in time_base' in frame:
                    timebase = frame['config in time_base'][:-1]
                if 'n' in frame and int(frame['n']) == slic['pattern_offset']:
                    slic['pts'] = int(frame['pts'])
                    slic['pts_time'] = float(frame['pts_time'])
                    break
            slic['timebase'] = timebase
            slices.append(slic)
        else:
            Logger.warning('Unable to create slice at {}\n'.format(draft_time))

        if draft_time + overlap_time + dur > duration:
            dur1 = duration - draft_time - overlap_time
    # vt.slices = [MediaFile.VideoTrack.Slice(_) for _ in slices]
    return slices


def test():
    from .combined_info import combined_info_mediafile
    from .ffmpeg_utils import FFMPEG_UTILS_TEST_FILE_AV
    mf = combined_info_mediafile(FFMPEG_UTILS_TEST_FILE_AV)
    slices = [MediaFile.VideoTrack.Slice(_) for _ in create_slices(mf)]
    pprint(slices)
