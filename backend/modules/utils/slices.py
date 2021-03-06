# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import os
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


def avg_filter(src, size):
    dst = []
    for i in range(len(src)):
        w = i - max(i-size, 0)
        v = 0.0
        for x in range(w+1):
            v += src[i-x]
        avg = v / float(w+1)
        dst.append(avg)
    return dst


def avg_filter_bkwd(src, size):
    src.reverse()
    dst = avg_filter(src, size)
    src.reverse()
    dst.reverse()
    return dst


def peaks(src):
    avg_fwd = avg_filter(src, 5)
    avg_bwd = avg_filter_bkwd(src, 5)
    res = []
    for i in range(len(src)):
        if i == 0 or i == len(src) - 1:
            res.append(0.0)
            continue
        res.append(2.0 * src[i] - avg_fwd[i-1] - avg_bwd[i+1])
    return res


def mediafile_split_points(
        mf: MediaFile, vti=0, number_of_slices=48, min_slice_duration=48, start_time=0.0, end_time=None, scan_time=2.0):
    vt: MediaFile.VideoTrack = mf.videoTracks[vti]
    if end_time is None:
        end_time = vt.duration
    duration = end_time - start_time
    print('Duration: {}'.format(duration))
    time_base = float(vt.time_base)
    scan_frames = int(scan_time * float(vt.fps))
    if duration <= 2*min_slice_duration:
        return []
    if duration/float(number_of_slices) < min_slice_duration:
        number_of_slices = (1 + int(duration)) / min_slice_duration
    Logger.log('Creating slices (alt)\nSource: {}\nDUration: {}\n Count: {}\n'.format(mf.source.path, duration, number_of_slices))

    filters = ';'.join([
        # Prepare frame B for ssim
        '[v]tblend=all_expr=B,format=yuv420p10le,scale=400:400[v1]',
        # Prepare frame A for ssim
        '[v]tblend=all_expr=A,format=yuv420p10le,scale=400:400[v2]',
        # Calculate SSIM
        '[v1][v2]ssim=-,showinfo'
    ])

    start_pts = int(start_time * float(vt.fps))
    print('Preview start pts: {}'.format(start_pts))
    # Get pts for 1st frame
    command1 = 'ffmpeg -y -nostats -ss {ss:.3f} -i {src} -map v:{vidx} -copyts -vframes 1 -vf showinfo -f null {devnull}'.format(
        ss=start_time,
        src=mf.source.path,
        vidx=vti,
        devnull=os.devnull
    )
    # print(command1)
    proc = Popen(command1.split(' '), stdout=PIPE, stderr=PIPE, shell=True)
    cap = proc.communicate()
    for line in cap[1].split(b'\n'):
        d = Parsers.parse_auto(line.decode())
        if d[0] == 'showinfo' and d[2] is not None:
            a =dict(d[2])
            start_pts = int(a['pts'])
            print('Got start pts: {}'.format(start_pts))
            break


    fragment_duration = duration/float(number_of_slices)

    result = {'timebase': vt.time_base}
    slices = [{
        'time': start_time,
        'cut_frame': 0,
        'cut_time': 0.0,
        'cut_pts': start_pts
    }]
    for slice_index in range(1, number_of_slices):
        draft_time = start_time + float(int(fragment_duration * float(slice_index)))

        # Logger.log('  creating slice at time: {0}\n'.format(draft_time))
        command1 = 'ffmpeg -y -nostats -ss {ss:.3f} -i {src} -map v:{vidx} -copyts -vframes {vframes} -filter_complex {filters} -f null {devnull}'.format(
            ss=draft_time,
            src=mf.source.path,
            vidx=vti,
            vframes=scan_frames,
            filters=filters,
            devnull=os.devnull
        )
        # print(command1)
        proc = Popen(command1.split(' '), stdout=PIPE, stderr=PIPE, shell=True)
        cap = proc.communicate()
        ssims = [0.5]
        for line in cap[0].split(b'\n'):
            d = Parsers.parse_line_headless(line.decode())
            if d:
                d = dict(d)
                if 'n' in d:
                    n = int(d['n'])
                    if n != len(ssims):
                        Logger.error('Non-monotonous N: {}'.format(n))
                    ssims.append(float(d['All']))
        infos = []
        for line in cap[1].split(b'\n'):
            d = Parsers.parse_auto(line.decode())
            if d[0] == 'showinfo' and d[2] is not None:
                infos.append(dict(d[2]))
        p = [int(pow(5*_, 2)) for _ in peaks(ssims)]
        # Search appropriate frame
        # default = middle of scanned area
        cut_frame = min(int(float(vt.fps)*scan_time/2.0) - 1, len(p) >> 1)
        decision = 0
        for i in range(2, len(p) - 2):
            if p[i] > 2 and p[i-1] == 0 and p[i+1] == 0:
                decision = p[i]
                cut_frame = i - 1
                break
        cut_time = time_base * float(infos[cut_frame]['pts'])
        print('Slice:{} time:{} cut_time:{:.3f} cut_frame_rel:{} cut_frame_abs:{} dec:{}'.format(
            slice_index, draft_time, cut_time, cut_frame, int(float(infos[cut_frame]['pts_time'])*float(vt.fps)), decision)
        )
        slice = {
            'time': draft_time,
            'cut_frame': cut_frame,
            'cut_time': cut_time,
            'cut_pts': infos[cut_frame]['pts_time']
        }
        slices.append(slice)
        # for line in cap[1].split(b'\n'):
        #     d = Parsers.ffmpeg_auto_text(line.decode())
        #     print(d)

        # trout = proc2.stderr.read().decode()
        # slic = {'time': draft_time}
        # for line in trout.split(';'):
        #     kv = line.strip().split('=', 1)
        #     if len(kv) == 2:
        #         vv = kv[1].split(',')
        #         if len(vv) == 1:
        #             slic[kv[0]] = int(kv[1])
        #         else:
        #             slic[kv[0]] = [int(_) for _ in vv]
        # if 'crc' in slic:
        #     command = 'ffmpeg -y -ss {start:.3f} -i {input} -copyts -r {fps} -vf showinfo -map v:{vti} -vframes {frames} -c:v rawvideo -f null {devnull}'.format(
        #         start=draft_time,
        #         input=mf.source.path,
        #         fps=vt.fps,
        #         vti=vti,
        #         frames=2 + slic['pattern_offset'],
        #         devnull=DEVNULL
        #     )
        #     proc = Popen(command.split(' '), stdout=PIPE, stderr=PIPE)
        #     while proc.poll() is None:
        #         time.sleep(0.1)
        #     output = proc.stderr.read().decode()
        #     parsed = Parsers.ffmpeg_auto_text(output)
        #     # Search pattern start frame
        #     Logger.warning('{}\n'.format(slic))
        #     for frame in parsed['showinfo'][0]:
        #         if timebase is None and 'config in time_base' in frame:
        #             timebase = frame['config in time_base'][:-1]
        #         if 'n' in frame and int(frame['n']) == slic['pattern_offset']:
        #             slic['pts'] = int(frame['pts'])
        #             slic['pts_time'] = float(frame['pts_time'])
        #             break
        #     slic['timebase'] = timebase
        #     slices.append(slic)
        # else:
        #     Logger.warning('Unable to create slice at {}\n'.format(draft_time))
        #
        # if draft_time + overlap_time + dur > duration:
        #     dur1 = duration - draft_time - overlap_time
    # vt.slices = [MediaFile.VideoTrack.Slice(_) for _ in slices]
    return result


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


def test2():
    from .combined_info import combined_info_mediafile
    from .ffmpeg_utils import FFMPEG_UTILS_TEST_FILE_AV
    import sys
    Logger.set_console_level(Logger.LogLevel.TRACE)
    print(sys.argv[1])
    mf = combined_info_mediafile(sys.argv[1])
    split = mediafile_split_points(mf, number_of_slices=28)
    # for s in split:
    # slices = [MediaFile.VideoTrack.Slice(_) for _ in create_slices(mf)]
    pprint(split)
    print([_['cut_frame_abs'] for _ in split])



if __name__ == '__main__':
    test()
