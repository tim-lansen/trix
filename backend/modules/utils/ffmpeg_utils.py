# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import re
import os
import sys
import copy
from pprint import pprint
from .parsers import Parsers, timecode_to_float
from .log_console import Logger
from subprocess import Popen, PIPE
from .pipe_nowait import pipe_nowait
from .combined_info import combined_info
from .slices import create_slices
from typing import List
from modules.models.mediafile import MediaFile
from modules.models.asset import Asset, Stream, VideoStream, AudioStream, SubStream


if os.name == 'nt':
    DEVNULL = 'nul'
    FFMPEG_UTILS_TEST_FILE_AVS = r'D:\storage\crude\watch\test.src.avs\test_src.AVS.mkv'
    FFMPEG_UTILS_TEST_FILE_AV = r'D:\storage\crude\watch\test.src\test_src.AV.mp4'
    FFMPEG_UTILS_TEST_FILE_A1 = r'D:\storage\crude\watch\test.src\test_src.A1.mkv'
    FFMPEG_UTILS_TEST_FILE_A2 = r'D:\storage\crude\watch\test.src\test_src.A2.mkv'
    FFMPEG_UTILS_STORAGE_TRANSIT = r'D:\storage\_transit'
    FFMPEG_UTILS_STORAGE_PREVIEW = r'D:\storage\_preview'
else:
    import fcntl
    DEVNULL = '/dev/null'
    FFMPEG_UTILS_TEST_FILE_AVS = '/mnt/server1_id/crude/watch/test.src.avs/test_src.AVS.mkv'
    FFMPEG_UTILS_TEST_FILE_AV = '/mnt/server1_id/crude/watch/test.src/test_src.AV.mp4'
    FFMPEG_UTILS_STORAGE_TRANSIT = '/mnt/server1_id/crude/_transit'
    FFMPEG_UTILS_STORAGE_PREVIEW = '/mnt/server1_id/crude/_preview'


def ffmpeg_cropdetect(url,  video_track: MediaFile.VideoTrack, cd_black=0.08, cd_round=4, cd_reset=40, frames=100):
    start = video_track.duration/12.0
    step = video_track.duration/11.0
    width = video_track.width
    height = video_track.height

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
        command = 'ffmpeg -y -ss {start:.2f} -i {src} -ss 3 -vsync 0 -copyts -vframes {vframes} -filter_complex [0:v:0]showinfo,cropdetect={cd0}:{cd1}:{cd2}[v] -map [v] -f null {nul}' \
                  ''.format(start=start0, src=url, vframes=frames, cd0=cd_black, cd1=2, cd2=cd_reset, nul=DEVNULL)
        Logger.debug('{}\n'.format(command))
        proc = Popen(command.split(' '), stderr=PIPE)
        while proc.poll() is None:
            lines = proc.stderr.readline().decode().split('\r')
            for line in lines:
                fn, parse = Parsers.parse_auto(line)
                if parse is None:
                    continue
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
    sar = video_track.par.val()
    return {'w': cdwc, 'h': cdhc, 'x': cdxc, 'y': cdyc, 'sar': sar, 'aspect': sar * float(cdwc)/float(cdhc)}


def ffmpeg_create_preview_extract_audio_subtitles(mediafile: MediaFile, dir_transit, dir_preview, que_progress=None):
    # First, call cropdetect
    if len(mediafile.videoTracks):
        cropdetect = ffmpeg_cropdetect(mediafile.source.path, mediafile.videoTracks[0])
        dur = mediafile.videoTracks[0].duration
    else:
        dur = mediafile.format.duration
    src = mediafile.source.path
    vout_arch: List[MediaFile] = []
    vout_refs: List[MediaFile] = []
    vout_trans: List[MediaFile] = []
    # advance_audio_index = 0 if len(mediafile.videoTracks) == 0 else len(mediafile.audioTracks)

    filters = []
    outputs = []
    # Enumerate video tracks, collect transformation filters and outputs

    for sti, v in enumerate(mediafile.videoTracks):
        preview = v.ref_add()
        preview.name = 'preview-video'
        vout_refs.append(preview)
        preview.source.path = os.path.join(dir_preview.net_path, '{}.v{}.preview.mp4'.format(mediafile.guid, sti))
        preview.source.url = '{}/{}.v{}.preview.mp4'.format(dir_preview.web_path, mediafile.guid, sti)
        outputs.append('-map [pv{sti}] -c:v libx264 -preset fast -g 20 -b:v 320k {path}'.format(sti=sti, path=preview.source.path))
        # vout_arch.append(mediafile)
        vp = preview.videoTracks[0]
        if sti == 0:
            filters.append('[0:v:{sti}]fps={fps},format=yuv420p,scale={pw}:{ph},blackdetect=d=0.5:pic_th=0.99:pix_th=0.005,showinfo[pv{sti}]'
                           ''.format(sti=sti, fps=v.fps, pw=vp.width, ph=vp.height))
        else:
            filters.append('[0:v:{sti}]format=yuv420p,scale={pw}:{ph}[pv{sti}]'.format(sti=sti, pw=vp.width, ph=vp.height))

    # Enumerate subtitles tracks, collect outputs for previews and extracted tracks
    for sti, s in enumerate(mediafile.subTracks):
        # Special case for 1-track subtitles only
        if len(mediafile.videoTracks) == 0 and len(mediafile.audioTracks) == 0 and len(mediafile.subTracks) == 1:
            subtitles = mediafile
            st = s
        else:
            st = copy.deepcopy(s)
            st.index = 0
            subtitles: MediaFile = MediaFile(name='transit subtitles')
            s.extract = subtitles.guid
            subtitles.master.set(mediafile.guid.guid)
            subtitles.subTracks.append(st)
            subtitles.source.path = os.path.join(dir_transit.net_path, '{}.s{:02d}.extract.mkv'.format(mediafile.guid, sti))
            outputs.append('-map 0:s:{sti} -c:s copy {path}'.format(sti=sti, path=subtitles.source.path))
            vout_trans.append(subtitles)
        # ci = 0
        subtitles_preview: MediaFile = MediaFile(name='preview-sub')
        vout_refs.append(subtitles_preview)
        subtitles_preview.master.set(subtitles.guid.guid)
        subtitles_preview.isPreview = True
        subtitles_preview.source.path = os.path.join(dir_preview.net_path, '{}.s{:02d}.preview.vtt'.format(subtitles.guid, sti))
        subtitles_preview.source.url = '{}/{}.s{:02d}.preview.vtt'.format(dir_preview.web_path, subtitles.guid, sti)
        outputs.append('-map 0:s:{sti} -c:s webvtt {path}'.format(sti=sti, path=subtitles_preview.source.path))
        st.previews.append(str(subtitles_preview.guid))

    # Enumerate audio tracks, collect pan filters and outputs for previews and extracted tracks
    for sti, a in enumerate(mediafile.audioTracks):
        # Special case for 1-track audio only
        if len(mediafile.videoTracks) == 0 and len(mediafile.subTracks) == 0 and len(mediafile.audioTracks) == 1:
            audio = mediafile
            at = a
        else:
            at = copy.deepcopy(a)
            audio: MediaFile = MediaFile(name='transit audio')
            a.extract = audio.guid
            audio.master.set(mediafile.guid.guid)
            audio.audioTracks.append(at)
            audio.source.path = os.path.join(dir_transit.net_path, '{}.a{:02d}.extract.mkv'.format(mediafile.guid, sti))
            outputs.append('-map 0:a:{sti} -c:a copy {path}'.format(sti=sti, path=audio.source.path))
            vout_trans.append(audio)
        # Add silencedetect filter for 1st audio track only
        audio_filter = None if sti else '[0:a:0]silencedetect,pan=mono|c0=c0[ap_00_00]'
        for ci in range(a.channels):
            audio_preview: MediaFile = MediaFile(name='preview-audio')
            vout_refs.append(audio_preview)
            audio_preview.master.set(audio.guid.guid)
            audio_preview.isPreview = True
            audio_preview.source.path = os.path.join(dir_preview.net_path, '{}.a{:02d}.c{:02d}.preview.mp4'.format(audio.guid, sti, ci))
            audio_preview.source.url = '{}/{}.a{:02d}.c{:02d}.preview.mp4'.format(dir_preview.web_path, audio.guid, sti, ci)
            if audio_filter is None:
                audio_filter = '[0:a:{sti}]pan=mono|c0=c{ci}[ap_{sti:02d}_{ci:02d}]'.format(sti=sti, ci=ci)
            filters.append(audio_filter)
            audio_filter = None
            outputs.append('-map [ap_{sti:02d}_{ci:02d}] -strict -2 -c:a aac -b:a 48k {path}'.format(sti=sti, ci=ci, path=audio_preview.source.path))
            at.previews.append(str(audio_preview.guid))

    # Finally, compose the command
    command_cli = 'ffmpeg -y -i {src} -map_metadata -1 -filter_complex "{filters}" {outputs}'.format(src=src, filters=';'.join(filters), outputs=' '.join(outputs))
    command_py = 'ffmpeg -y -i {src} -map_metadata -1 -filter_complex {filters} {outputs}'.format(src=src, filters=';'.join(filters), outputs=' '.join(outputs))

    Logger.log('{}\n'.format(command_cli))

    # Create dirs if needed
    if len(vout_refs) and not os.path.isdir(dir_preview.net_path):
        Logger.log('Creating dir: {}\n'.format(dir_preview.net_path))
        os.makedirs(dir_preview.net_path)
    if len(vout_trans) and not os.path.isdir(dir_transit.net_path):
        Logger.log('Creating dir: {}\n'.format(dir_transit.net_path))
        os.makedirs(dir_transit.net_path)

    proc = Popen(command_py.split(' '), stdin=sys.stdin, stderr=PIPE)
    pipe_nowait(proc.stderr)
    stde = proc.stderr.fileno()
    tail = ''

    blacks = []
    silences = []
    # 'frames' will contain filtered showinfo
    frames = {'iframes': [], 'frames': []}
    pts_time = 0.0
    pts_start = None

    while proc.poll() is None:
        lines = []
        try:
            part = tail + os.read(stde, 65536).decode().replace('\r', '\n').replace('\n\n', '\n')
            lines = part.split('\n')
            if len(lines):
                tail = lines.pop(-1)
        except OSError as e:
            pass
        for line in lines:
            fn, parse = Parsers.parse_auto(line)
            if fn is None or parse is None:
                continue
            if fn == 'showinfo':
                pts_time = float(parse['pts_time'])
                if pts_start is None:
                    pts_start = pts_time
                if parse['iskey'] == 1:
                    frames['iframes'].append(parse)
            elif fn == 'blackdetect':
                blacks += [[float(parse['black_start']), -1], [float(parse['black_end']), 1]]
            elif fn == 'silencedetect':
                if 'silence_start' in parse:
                    silences.append([float(parse['silence_start']), -1])
                elif 'silence_end' in parse:
                    if len(silences) == 0:
                        silences.append([pts_start, -1])
                    silences.append([float(parse['silence_end']), 1])
                    # else:
                    #     Logger.warning('silencedetect: silence_end without silence_start\n')
            elif fn == 'progress':
                progress = timecode_to_float(parse['time']) / dur
                if que_progress:
                    que_progress.put({'time': progress})
                else:
                    Logger.log('progress {}%     \r'.format(int(100.0 * progress)))
            else:
                Logger.log('{}: {}\n'.format(fn, parse))

    if len(silences) > 0 and len(silences[-1]) == 1:
        silences[-1].append(pts_time)

    # Merge blacks and silence to find dark silent blocks
    # Guess program in and out
    program_in = pts_start
    program_out = pts_time

    # Create asset
    asset: Asset = Asset()
    # Add main source
    asset.mediaFiles.append(mediafile.guid)
    # Add trans source(s)
    asset.mediaFiles += [_.guid for _ in vout_trans]

    # Add main video stream and auto-detected params
    if len(mediafile.videoTracks):
        if len(blacks):
            bound_in = min(program_out / 2.0, 200.0)
            bound_out = program_out / 2.0
            s = 2 if len(silences) else 1
            silent_dark = False
            for bs in sorted(blacks + silences):
                s += bs[1]
                if s == 0:
                    silent_dark = True
                    # Set program_out only once!
                    if program_out > bs[0] > bound_out:
                        program_out = bs[0]
                    continue
                if silent_dark:
                    silent_dark = False
                    if bs[0] < bound_in:
                        program_in = bs[0]
            Logger.log('Guessed program IN: {:.2f},  OUT: {:.2f}\n'.format(program_in, program_out))

        v_stream = VideoStream()
        v_stream.program_in = program_in
        v_stream.program_out = program_out
        v_stream.cropdetect.update_json(cropdetect)
        v_stream.channels.append(Stream.Channel())
        asset.videoStreams.append(v_stream)

    # Add audio stream(s)
    for ti, a in enumerate(mediafile.audioTracks):
        # asset.mediaFiles.append(trans.guid)
        channels = a.channels
        a_stream = AudioStream()
        a_stream.program_in = program_in
        a_stream.program_out = program_out
        a_stream.layout = a.channel_layout
        if a.tags and a.tags.language:
            a_stream.language = a.tags.language
        for ci in range(channels):
            chan = Stream.Channel()
            chan.src_stream_index = ti
            chan.src_channel_index = ci
            a_stream.channels.append(chan)
        asset.audioStreams.append(a_stream)

    # Add audio track(s)
    # for ti, trans in enumerate(vout_trans):
    #     asset.mediaFiles.append(trans.guid)
    #     channels = trans.audioTracks[0].channels
    #     a_stream = AudioStream()
    #     a_stream.program_in = program_in
    #     a_stream.program_out = program_out
    #     # a_stream.layout = AudioStream.Layout.DEFAULT[channels]
    #     a_stream.layout = trans.audioTracks[0].channel_layout
    #     for ci in range(channels):
    #         chan = Stream.Channel()
    #         chan.src_stream_index = ti + advance_audio_index
    #         chan.src_channel_index = ci
    #         a_stream.channels.append(chan)
    #     asset.audioStreams.append(a_stream)

    # Update info for every mediafile
    for mf in vout_arch + vout_refs + vout_trans:
        if mf.format.stream_count is None:
            Logger.info('Updating info for file {} / '.format(mf.guid))
            combined_info(mf)
            Logger.info('{}\n'.format(mf.guid))

    # Return complex object
    return {
        'src': mediafile,
        'asset': asset,
        'trans': vout_trans,
        'previews': vout_refs,
        'archives': vout_arch
    }


def ffmpeg_cpeas_slice(mediafile: MediaFile, job_group, dir_transit, dir_preview, dir_cache, que_progress=None):
    # First, call cropdetect
    if len(mediafile.videoTracks):
        # cropdetect = ffmpeg_cropdetect(mediafile.source.path, mediafile.videoTracks[0])
        dur = mediafile.videoTracks[0].duration
    else:
        dur = mediafile.format.duration
    src = mediafile.source.path
    # vout_arch: List[MediaFile] = []
    # vout_refs: List[MediaFile] = []
    # vout_trans: List[MediaFile] = []
    # advance_audio_index = 0 if len(mediafile.videoTracks) == 0 else len(mediafile.audioTracks)

    filters = []
    outputs = []
    slices = []
    # Enumerate video tracks, collect slices

    for sti, v in enumerate(mediafile.videoTracks):
        preview = v.ref_add()
        preview.name = 'preview-video'
        preview.source.path = os.path.join(dir_preview.net_path, '{}.v{}.preview.mp4'.format(mediafile.guid, sti))
        preview.source.url = '{}/{}.v{}.preview.mp4'.format(dir_preview.web_path, mediafile.guid, sti)
        slcs = create_slices(mediafile, sti)
        slices.append(slcs)
    return slices


def ffmpeg_eas(mediafile: MediaFile, dir_transit, dir_preview, que_progress=None):
    # Ignore video tracks
    src = mediafile.source.path
    out_refs: List[MediaFile] = []
    out_trans: List[MediaFile] = []

    filters = []
    outputs = []

    # Enumerate subtitles tracks, collect outputs for previews and extracted tracks
    for sti, s in enumerate(mediafile.subTracks):
        # Special case for 1-track subtitles only
        if len(mediafile.videoTracks) == 0 and len(mediafile.audioTracks) == 0 and len(mediafile.subTracks) == 1:
            subtitles = mediafile
            st = s
        else:
            st = copy.deepcopy(s)
            st.index = 0
            subtitles = MediaFile(name='transit subtitles')
            s.extract = subtitles.guid
            subtitles.master.set(mediafile.guid.guid)
            subtitles.subTracks.append(st)
            subtitles.source.path = os.path.join(dir_transit.net_path,
                                             '{}.s{:02d}.extract.mkv'.format(mediafile.guid, sti))
            outputs.append('-map 0:s:{sti} -c:s copy {path}'.format(sti=sti, path=subtitles.source.path))
            sout_trans.append(subtitles)
        # ci = 0
        subtitles_preview = MediaFile(name='preview-sub')
        sout_refs.append(subtitles_preview)
        subtitles_preview.master.set(subtitles.guid.guid)
        subtitles_preview.isPreview = True
        subtitles_preview.source.path = os.path.join(dir_preview.net_path,
                                                 '{}.s{:02d}.preview.vtt'.format(subtitles.guid, sti))
        subtitles_preview.source.url = '{}/{}.s{:02d}.preview.vtt'.format(dir_preview.web_path, subtitles.guid, sti)
        outputs.append('-map 0:s:{sti} -c:s webvtt {path}'.format(sti=sti, path=subtitles_preview.source.path))
        st.previews.append(str(subtitles_preview.guid))

    # Enumerate audio tracks, collect pan filters and outputs for previews and extracted tracks
    for sti, a in enumerate(mediafile.audioTracks):
        # Special case for 1-track audio only
        if len(mediafile.videoTracks) == 0 and len(mediafile.subTracks) == 0 and len(mediafile.audioTracks) == 1:
            audio = mediafile
            at = a
        else:
            at = copy.deepcopy(a)
            audio = MediaFile(name='transit audio')
            a.extract = audio.guid
            audio.master.set(mediafile.guid.guid)
            audio.audioTracks.append(at)
            audio.source.path = os.path.join(dir_transit.net_path, '{}.a{:02d}.extract.mkv'.format(mediafile.guid, sti))
            outputs.append('-map 0:a:{sti} -c:a copy {path}'.format(sti=sti, path=audio.source.path))
            aout_trans.append(audio)
        # Add silencedetect filter for 1st audio track only
        audio_filter = None if sti else '[0:a:0]silencedetect,pan=mono|c0=c0[ap_00_00]'
        for ci in range(a.channels):
            audio_preview = MediaFile(name='preview-audio')
            aout_refs.append(audio_preview)
            audio_preview.master.set(audio.guid.guid)
            audio_preview.isPreview = True
            audio_preview.source.path = os.path.join(dir_preview.net_path, '{}.a{:02d}.c{:02d}.preview.mp4'.format(audio.guid, sti, ci))
            audio_preview.source.url = '{}/{}.a{:02d}.c{:02d}.preview.mp4'.format(dir_preview.web_path, audio.guid, sti, ci)
            if audio_filter is None:
                audio_filter = '[0:a:{sti}]pan=mono|c0=c{ci}[ap_{sti:02d}_{ci:02d}]'.format(sti=sti, ci=ci)
            filters.append(audio_filter)
            audio_filter = None
            outputs.append('-map [ap_{sti:02d}_{ci:02d}] -strict -2 -c:a aac -b:a 48k {path}'.format(sti=sti, ci=ci, path=audio_preview.source.path))
            at.previews.append(str(audio_preview.guid))

    # Finally, compose the command
    command_cli = 'ffmpeg -y -i {src} -map_metadata -1 -filter_complex "{filters}" {outputs}'.format(src=src, filters=';'.join(filters), outputs=' '.join(outputs))
    command_py = 'ffmpeg -y -i {src} -map_metadata -1 -filter_complex {filters} {outputs}'.format(src=src, filters=';'.join(filters), outputs=' '.join(outputs))

    Logger.log('{}\n'.format(command_cli))

    # Create dirs if needed
    if len(out_refs) and not os.path.isdir(dir_preview.net_path):
        Logger.log('Creating dir: {}\n'.format(dir_preview.net_path))
        os.makedirs(dir_preview.net_path)
    if len(out_trans) and not os.path.isdir(dir_transit.net_path):
        Logger.log('Creating dir: {}\n'.format(dir_transit.net_path))
        os.makedirs(dir_transit.net_path)

    proc = Popen(command_py.split(' '), stdin=sys.stdin, stderr=PIPE)
    pipe_nowait(proc.stderr)
    stde = proc.stderr.fileno()
    tail = ''

    silences = []
    pts_time = 0.0
    pts_start = None

    while proc.poll() is None:
        lines = []
        try:
            part = tail + os.read(stde, 65536).decode().replace('\r', '\n').replace('\n\n', '\n')
            lines = part.split('\n')
            if len(lines):
                tail = lines.pop(-1)
        except OSError as e:
            pass
        for line in lines:
            fn, parse = Parsers.parse_auto(line)
            if fn is None or parse is None:
                continue
            if fn == 'showinfo':
                pts_time = float(parse['pts_time'])
                if pts_start is None:
                    pts_start = pts_time
            elif fn == 'silencedetect':
                if 'silence_start' in parse:
                    silences.append([float(parse['silence_start']), -1])
                elif 'silence_end' in parse:
                    if len(silences) == 0:
                        silences.append([pts_start, -1])
                    silences.append([float(parse['silence_end']), 1])
            elif fn == 'progress':
                progress = timecode_to_float(parse['time']) / dur
                if que_progress:
                    que_progress.put({'progress': progress})
                else:
                    Logger.log('progress {}%     \r'.format(int(100.0 * progress)))
            else:
                Logger.log('{}: {}\n'.format(fn, parse))

    if len(silences) > 0 and len(silences[-1]) == 1:
        silences[-1].append(pts_time)

    # Merge blacks and silence to find dark silent blocks
    # Guess program in and out
    program_in = pts_start
    program_out = pts_time

    # Create asset
    asset = Asset()
    # Add main source
    asset.mediaFiles.append(mediafile.guid)
    # Add trans source(s)
    asset.mediaFiles += [_.guid for _ in out_trans]

    # Add main video stream and auto-detected params
    if len(mediafile.videoTracks):
        v_stream = VideoStream()
        v_stream.program_in = program_in
        v_stream.program_out = program_out
        v_stream.cropdetect.update_json(cropdetect)
        v_stream.channels.append(Stream.Channel())
        asset.videoStreams.append(v_stream)

    # Add audio stream(s)
    for ti, a in enumerate(mediafile.audioTracks):
        # asset.mediaFiles.append(trans.guid)
        channels = a.channels
        a_stream = AudioStream()
        a_stream.program_in = program_in
        a_stream.program_out = program_out
        a_stream.layout = a.channel_layout
        if a.tags and a.tags.language:
            a_stream.language = a.tags.language
        for ci in range(channels):
            chan = Stream.Channel()
            chan.src_stream_index = ti
            chan.src_channel_index = ci
            a_stream.channels.append(chan)
        asset.audioStreams.append(a_stream)

    # Add audio track(s)
    # for ti, trans in enumerate(vout_trans):
    #     asset.mediaFiles.append(trans.guid)
    #     channels = trans.audioTracks[0].channels
    #     a_stream = AudioStream()
    #     a_stream.program_in = program_in
    #     a_stream.program_out = program_out
    #     # a_stream.layout = AudioStream.Layout.DEFAULT[channels]
    #     a_stream.layout = trans.audioTracks[0].channel_layout
    #     for ci in range(channels):
    #         chan = Stream.Channel()
    #         chan.src_stream_index = ti + advance_audio_index
    #         chan.src_channel_index = ci
    #         a_stream.channels.append(chan)
    #     asset.audioStreams.append(a_stream)

    # Update info for every mediafile
    for mf in vout_arch + vout_refs + vout_trans:
        if mf.format.stream_count is None:
            Logger.info('Updating info for file {} / '.format(mf.guid))
            combined_info(mf)
            Logger.info('{}\n'.format(mf.guid))

    # Return complex object
    return {
        'src': mediafile,
        'asset': asset,
        'trans': vout_trans,
        'previews': vout_refs,
        'archives': vout_arch
    }


def ffmpeg_create_archive_preview_extract_audio_subtitles(mediafile: MediaFile, dir_transit, dir_preview, que_progress=None):
    # First, call cropdetect
    if len(mediafile.videoTracks):
        cropdetect = ffmpeg_cropdetect(mediafile.source.path, mediafile.videoTracks[0])
        dur = mediafile.videoTracks[0].duration
    else:
        dur = mediafile.format.duration
    src = mediafile.source.path
    vout_arch: List[MediaFile] = []
    vout_refs: List[MediaFile] = []
    vout_trans: List[MediaFile] = []
    advance_audio_index = 0 if len(mediafile.videoTracks) == 0 else len(mediafile.audioTracks)

    filters = []
    outputs = []
    # Enumerate video tracks, collect transformation filters and outputs

    # Version for

    for sti, v in enumerate(mediafile.videoTracks):
        preview = v.ref_add()
        vt = copy.deepcopy(v)
        # preview = vt.ref_add()
        preview.name = 'preview'
        vout_refs.append(preview)
        preview.source.path = os.path.join(dir_preview.net_path, '{}.v{}.preview.mp4'.format(mediafile.guid, sti))
        preview.source.url = '{}/{}.v{}.preview.mp4'.format(dir_preview.web_path, mediafile.guid, sti)
        # preview.source.url
        outputs.append(
            '-map [pv{sti}] -c:v libx264 -preset fast -g 20 -b:v 320k {path}'.format(sti=sti, path=preview.source.path))
        arch = MediaFile()
        arch.videoTracks.append(vt)
        # vout_arch.append(arch)
        vout_arch.append(mediafile)
        vp = preview.videoTracks[0]
        if sti == 0:
            filters.append(
                '[0:v:{sti}]fps={fps},format=yuv420p,scale={pw}:{ph},blackdetect=d=0.5:pic_th=0.99:pix_th=0.005,showinfo[pv{sti}]'
                ''.format(sti=sti, fps=v.fps, pw=vp.width, ph=vp.height))
        else:
            filters.append(
                '[0:v:{sti}]format=yuv420p,scale={pw}:{ph}[pv{sti}]'.format(sti=sti, pw=vp.width, ph=vp.height))

    # Enumerate audio tracks, collect pan filters and outputs for previews and extracted tracks
    for sti, a in enumerate(mediafile.audioTracks):
        # Special case for 1-track audio only
        if len(mediafile.videoTracks) == 0 and len(mediafile.subTracks) == 0 and len(mediafile.audioTracks) == 1:
            audio = mediafile
            at = a
        else:
            at = copy.deepcopy(a)
            audio = MediaFile(name='transit audio')
            a.extract = audio.guid
            audio.master.set(mediafile.guid.guid)
            audio.audioTracks.append(at)
            audio.source.path = os.path.join(dir_transit.net_path, '{}.a{:02d}.extract.mkv'.format(mediafile.guid, sti))
            outputs.append('-map 0:a:{sti} -c:a copy {path}'.format(sti=sti, path=audio.source.path))
        vout_trans.append(audio)
        # Add silencedetect filter for 1st audio track only
        audio_filter = None if sti else '[0:a:0]silencedetect,pan=mono|c0=c0[ap_00_00]'
        for ci in range(a.channels):
            audio_preview = MediaFile(name='preview audio')
            vout_refs.append(audio_preview)
            audio_preview.master.set(audio.guid.guid)
            audio_preview.isPreview = True
            audio_preview.source.path = os.path.join(dir_preview.net_path,
                                                     '{}.a{:02d}.c{:02d}.preview.mp4'.format(audio.guid, sti, ci))
            audio_preview.source.url = '{}/{}.a{:02d}.c{:02d}.preview.mp4'.format(dir_preview.web_path, audio.guid, sti,
                                                                                  ci)
            if audio_filter is None:
                audio_filter = '[0:a:{sti}]pan=mono|c0=c{ci}[ap_{sti:02d}_{ci:02d}]'.format(sti=sti, ci=ci)
            filters.append(audio_filter)
            audio_filter = None
            outputs.append('-map [ap_{sti:02d}_{ci:02d}] -strict -2 -c:a aac -b:a 48k {path}'.format(sti=sti, ci=ci,
                                                                                                     path=audio_preview.source.path))
            at.previews.append(str(audio_preview.guid))

    # Finally, compose the command
    command_cli = 'ffmpeg -y -i {src} -map_metadata -1 -filter_complex "{filters}" {outputs}'.format(src=src,
                                                                                                     filters=';'.join(
                                                                                                         filters),
                                                                                                     outputs=' '.join(
                                                                                                         outputs))
    command_py = 'ffmpeg -y -i {src} -map_metadata -1 -filter_complex {filters} {outputs}'.format(src=src,
                                                                                                  filters=';'.join(
                                                                                                      filters),
                                                                                                  outputs=' '.join(
                                                                                                      outputs))

    Logger.log('{}\n'.format(command_cli))

    # Create dirs if needed
    if len(vout_refs) and not os.path.isdir(dir_preview.net_path):
        Logger.log('Creating dir: {}\n'.format(dir_preview.net_path))
        os.makedirs(dir_preview.net_path)
    if len(vout_trans) and not os.path.isdir(dir_transit.net_path):
        Logger.log('Creating dir: {}\n'.format(dir_transit.net_path))
        os.makedirs(dir_transit.net_path)

    proc = Popen(command_py.split(' '), stdin=sys.stdin, stderr=PIPE)
    pipe_nowait(proc.stderr)
    stde = proc.stderr.fileno()
    tail = ''

    blacks = []
    silences = []
    # 'frames' will contain filtered showinfo
    frames = {'iframes': [], 'frames': []}
    pts_time = 0.0
    pts_start = None

    while proc.poll() is None:
        lines = []
        try:
            part = tail + os.read(stde, 65536).decode().replace('\r', '\n').replace('\n\n', '\n')
            lines = part.split('\n')
            if len(lines):
                tail = lines.pop(-1)
        except OSError as e:
            pass
        for line in lines:
            fn, parse = Parsers.parse_auto(line)
            if fn is None or parse is None:
                continue
            if fn == 'showinfo':
                pts_time = float(parse['pts_time'])
                if pts_start is None:
                    pts_start = pts_time
                if parse['iskey'] == 1:
                    frames['iframes'].append(parse)
            elif fn == 'blackdetect':
                blacks += [[float(parse['black_start']), -1], [float(parse['black_end']), 1]]
            elif fn == 'silencedetect':
                if 'silence_start' in parse:
                    silences.append([float(parse['silence_start']), -1])
                elif 'silence_end' in parse:
                    if len(silences) == 0:
                        silences.append([pts_start, -1])
                    silences.append([float(parse['silence_end']), 1])
                    # else:
                    #     Logger.warning('silencedetect: silence_end without silence_start\n')
            elif fn == 'progress':
                progress = timecode_to_float(parse['time']) / dur
                if que_progress:
                    que_progress.put({'time': progress})
                else:
                    Logger.log('progress {}%     \r'.format(int(100.0 * progress)))
            else:
                Logger.log('{}: {}\n'.format(fn, parse))

    if len(silences) > 0 and len(silences[-1]) == 1:
        silences[-1].append(pts_time)

    # Merge blacks and silence to find dark silent blocks
    # Guess program in and out
    program_in = pts_start
    program_out = pts_time

    # Create asset
    asset = Asset()
    # Add main video track and auto-detected params
    if len(vout_arch):
        if len(blacks):
            bound_in = min(program_out / 2.0, 200.0)
            bound_out = program_out / 2.0
            s = 2 if len(silences) else 1
            silent_dark = False
            for bs in sorted(blacks + silences):
                s += bs[1]
                if s == 0:
                    silent_dark = True
                    # Set program_out only once!
                    if program_out > bs[0] > bound_out:
                        program_out = bs[0]
                    continue
                if silent_dark:
                    silent_dark = False
                    if bs[0] < bound_in:
                        program_in = bs[0]
            Logger.log('Guessed program IN: {:.2f},  OUT: {:.2f}\n'.format(program_in, program_out))

        asset.mediaFiles.append(mediafile.guid)
        # asset.mediaFiles.append(vout_arch[0].guid)
        v_stream = VideoStream()
        v_stream.program_in = program_in
        v_stream.program_out = program_out
        v_stream.cropdetect.update_json(cropdetect)
        v_stream.channels.append(Stream.Channel())
        asset.videoStreams.append(v_stream)
    # Add audio track(s)
    for ti, trans in enumerate(vout_trans):
        asset.mediaFiles.append(trans.guid)
        channels = trans.audioTracks[0].channels
        a_stream = AudioStream()
        a_stream.program_in = program_in
        a_stream.program_out = program_out
        # a_stream.layout = AudioStream.Layout.DEFAULT[channels]
        a_stream.layout = trans.audioTracks[0].channel_layout
        for ci in range(channels):
            chan = Stream.Channel()
            chan.src_stream_index = ti + advance_audio_index
            chan.src_channel_index = ci
            a_stream.channels.append(chan)
        asset.audioStreams.append(a_stream)

    # Update info for every mediafile
    for mf in vout_arch + vout_refs + vout_trans:
        if mf.format.stream_count is None:
            combined_info(mf)

    # Return complex object
    return {
        'asset': asset,
        'trans': vout_trans,
        'previews': vout_refs,
        'archives': vout_arch
    }


def test_ffmpeg_cropdetect():
    from .combined_info import combined_info_mediafile
    mf = combined_info_mediafile(FFMPEG_UTILS_TEST_FILE_AVS)
    Logger.warning('Combined info:\n{}\n'.format(mf.videoTracks[0].dumps(indent=2)))
    cd = VideoStream.Cropdetect()
    cd.update_json(ffmpeg_cropdetect(mf.source.path, mf.videoTracks[0]))
    Logger.log('Cropdetect:\n{}\n'.format(cd.dumps(indent=2)))


def test_ffmpeg_create_preview_extract_audio_subtitles():
    from .combined_info import combined_info_mediafile
    from modules.config.trix_config import TrixConfig
    mf = combined_info_mediafile(FFMPEG_UTILS_TEST_FILE_AVS)
    print(mf.dumps(indent=2, expose_unmentioned=True))
    dir_tr = TrixConfig.Storage.Server.Path(net_path=FFMPEG_UTILS_STORAGE_TRANSIT)
    dir_pr = TrixConfig.Storage.Server.Path(net_path=FFMPEG_UTILS_STORAGE_PREVIEW)
    result = ffmpeg_create_preview_extract_audio_subtitles(mf, dir_tr, dir_pr)
    Logger.debug('asset:\n{}\n'.format(result['asset'].dumps(indent=2)))
    Logger.debug('trans:\n{}\n'.format('\n'.join([_.dumps(indent=2) for _ in result['trans']])))
    Logger.debug('previews:\n{}\n'.format('\n'.join([_.dumps(indent=2) for _ in result['previews']])))
    Logger.debug('archives:\n{}\n'.format('\n'.join([_.dumps(indent=2) for _ in result['archives']])))
