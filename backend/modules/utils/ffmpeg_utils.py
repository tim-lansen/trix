# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import re
import os
import sys
import copy
from .parsers import Parsers
from .log_console import Logger
from subprocess import Popen, PIPE
from typing import List
from modules.models.mediafile import MediaFile
try:
    import fcntl
    DEVNULL = '/dev/null'
except:
    DEVNULL = 'nul'
    pass


def ffmpeg_cropdetect(mediafile: MediaFile, cd_black=0.08, cd_round=4, cd_reset=40, vframes=1):
    vt = mediafile.videoTracks[0]
    start = vt.Duration/12.0
    step = vt.Duration/11.0
    width = vt.width
    height = vt.height

    cdwc = 0
    cdhc = 0
    cdxc = 60000
    cdyc = 60000

    def _round(w, x, r):
        a = w % r
        if a:
            x += a/2
            w -= a
        return w, x

    for i in range(1, 10):
        cdwb = 0
        cdhb = 0
        cdxb = 50000
        cdyb = 50000
        start0 = int(start - 3)
        command = 'ffmpeg -y -ss {start:.2f} -i {src} -map v:0 -ss 3 -vsync 0 -copyts -vframes {vframes} -vf showinfo,cropdetect={cd0}:{cd1}:{cd2} -f null {nul}' \
                  ''.format(start=start0, src=mediafile.source.url, vframes=vframes, cd0=cd_black, cd1=cd_round, cd2=cd_reset, nul=DEVNULL)
        Logger.debug('{}\n'.format(command))
        proc = Popen(command.split(' '), stderr=PIPE)
        while proc.poll() is None:
            lines = proc.stderr.readline().decode().split('\r')
            for line in lines:
                fn, parse = Parsers.parse_auto(line)
                if fn == 'cropdetect':
                    # Workaround neg CD values: there may be no 'w', 'x' or 'h', 'y' keys
                    if 'h' in parse:
                        cdha, cdya = _round(parse['h'], parse['y'], cd_round)
                        cdhb = max(cdhb, cdha)
                        cdyb = min(cdyb, cdya)
                    if 'w' in parse:
                        cdwa, cdxa = _round(parse['w'], parse['x'], cd_round)
                        cdwb = max(cdwb, cdwa)
                        cdxb = min(cdxb, cdxa)
                # elif fn == 'showinfo':
                #     if 'pts' in parse:
                #         Logger.log('{}: {}\n'.format(fn, parse['pts']))
                #     else:
                #         Logger.log('{}\n'.format(repr(line)))
                # TODO: calculate fps from
        Logger.info('ffmpeg_cropdetect: pass {0} start {1} crop={2}:{3}:{4}:{5}\n'.format(i, start, cdwb, cdhb, cdxb, cdyb))
        if cdwb == cdwc and cdhb == cdhc and cdxb == cdxc and cdyb == cdyc:
            break
        cdwc = max(cdwb, cdwc)
        cdhc = max(cdhb, cdhc)
        cdxc = min(cdxb, cdxc)
        cdyc = min(cdyb, cdyc)
        if cdwb == width and cdhb == height:
            break
        start += step
    # Continue workaround neg CD values
    if cdxc > width:
        cdxc = 0
        cdwc = width
    if cdyc > height:
        cdyc = 0
        cdhc = height
    sar = vt.par.val()
    vt.cropdetect.update_json({'w': cdwc, 'h': cdhc, 'x': cdxc, 'y': cdyc, 'sar': sar, 'aspect': sar * float(cdwc)/float(cdhc)})


def ffmpeg_create_preview_extract_audio_subtitles(mediafile: MediaFile, dir_transit, dir_preview, cropdetect=True):
    # First, call cropdetect
    if mediafile.videoTracks[0].cropdetect is None and cropdetect:
        ffmpeg_cropdetect(mediafile)
    src = mediafile.source.url
    # vout_arch: List[MediaFile] = []
    # vout_refs: List[MediaFile] = []
    filters = []
    outputs = []
    # Enumerate video tracks, collect transformation filters and outputs
    for sti, v in enumerate(mediafile.videoTracks):
        vt = copy.deepcopy(v)
        preview = vt.ref_add()
        preview.source.url = os.path.join(dir_preview, '{}.v{}.preview.mp4'.format(mediafile.guid, sti))
        # vout_refs.append(preview)
        # arch = MediaFile()
        # arch.videoTracks.append(va)
        # vout_arch.append(arch)
        vp = preview.videoTracks[0]
        if sti == 0:
            filters.append('[0:v:{sti}]fps={fps},format=yuv420p,scale={pw}:{ph},blackdetect=d=0.5:pic_th=0.99:pix_th=0.005,showinfo[pv{sti}]'
                           ''.format(sti=sti, fps=v.fps, pw=vp.width, ph=vp.height))
        else:
            filters.append('[0:v:{sti}]format=yuv420p,scale={pw}:{ph}[pv{sti}]'.format(sti=sti, pw=vp.width, ph=vp.height))
        outputs.append('-map [pv{sti}] -c:v libx264 -preset fast -g 20 -b:v 320k {path}'.format(sti=sti, path=preview.source.url))

    # Enumerate audio tracks, collect pan filters and outputs for previews and extracts
    for sti, a in enumerate(mediafile.audioTracks):
        at = copy.deepcopy(a)
        audio = MediaFile()
        audio.guid.new()
        audio.master.set(mediafile.guid.guid)
        audio.audioTracks.append(at)
        audio.source.url = os.path.join(dir_transit, '{}.a{:02d}.extract.mkv'.format(mediafile.guid, sti))
        outputs.append('-map 0:a:{sti} -c:a copy {path}'.format(sti=sti, path=audio.source.url))
        # Add silencedetect filter for 1st audio track only
        if sti == 0:
            filters.append('[0:a:0]silencedetect')
        for ci in range(a.channels):
            audio_preview = MediaFile()
            audio_preview.guid.new()
            audio_preview.master.set(audio.guid.guid)
            audio_preview.isRef = True
            audio_preview.source.url = os.path.join(dir_preview, '{}.a{:02d}.c{:02d}.preview.mp4'.format(audio.guid, sti, ci))
            filters.append('[0:a:{sti}]pan=mono|c0=c{ci}[ap_{sti}_{ci}]'.format(sti=sti, ci=ci))
            outputs.append('-map [ap_{sti}_{ci}] -c:a aac -b:a 48k {path}'.format(sti=sti, ci=ci, path=audio_preview.source.url))
            at.refs.append(str(audio_preview.guid))

    # Finally, compose the command
    command_cli = 'ffmpeg -y -strict -2 -i {src} -filter_complex "{filters}" {outputs}'.format(src=src, filters=';'.join(filters), outputs=' '.join(outputs))
    command_py = 'ffmpeg -y -strict -2 -i {src} -filter_complex {filters} {outputs}'.format(src=src, filters=';'.join(filters), outputs=' '.join(outputs))

    Logger.log('{}\n'.format(command_cli))

    proc = Popen(command_py.split(' '), stdin=sys.stdin, stderr=PIPE)
    # 'blacks' will contain pairs [in, dur] of black
    blacks = []
    silencedetect = []
    # 'frames' will contain filtered showinfo
    frames = {'iframes': [], 'frames': []}
    pts_time = 0.0
    pts_start = None
    while proc.poll() is None:
        lines = proc.stderr.readline().decode().split('\r')
        for line in lines:
            fn, parse = Parsers.parse_auto(line)
            if fn is None or parse is None:
                continue
            if fn == 'showinfo':
                pts_time = parse['pts_time']
                if pts_start is None:
                    pts_start = pts_time
                if parse['iskey'] == 1:
                    frames['iframes'].append(parse)
            elif fn == 'blackdetect':
                blacks.append([parse['black_start'], parse['black_end']])
            elif fn == 'silencedetect':
                if 'silence_start' in parse:
                    silencedetect.append([float(parse['silence_start'])])
                elif 'silence_end' in parse:
                    if len(silencedetect) == 0:
                        silencedetect.append([pts_start, float(parse['silence_end'])])
                    elif len(silencedetect[-1]) == 1:
                        silencedetect[-1].append(float(parse['silence_end']))
                    else:
                        Logger.warning('silencedetect: silence_end without silence_start\n')
            else:
                Logger.log('{}: {}\n'.format(fn, parse))
    if len(silencedetect) > 0 and len(silencedetect[-1]) == 1:
        silencedetect[-1].append(pts_time)
    print(blacks)
    print(silencedetect)


def test_ffmpeg_cropdetect():
    from .combined_info import combined_info_mediafile
    mf = combined_info_mediafile(r'F:\storage\crude\watch\test.src\test_src.AV.mp4')
    ffmpeg_cropdetect(mf)
    Logger.warning('{}\n'.format(mf.videoTracks[0].dumps(indent=2)))


def test_ffmpeg_create_preview_extract_audio_subtitles():
    from .combined_info import combined_info_mediafile
    mf = combined_info_mediafile(r'F:\storage\crude\watch\test.src\test_src.AV.mp4')
    ffmpeg_create_preview_extract_audio_subtitles(mf, r'F:\storage\_transit', r'F:\storage\_preview', cropdetect=False)
