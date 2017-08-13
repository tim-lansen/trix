# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import os
from typing import List
from modules.models.mediafile import MediaFile
from modules.utils.log_console import Logger
from modules.utils.combined_info import combined_info_mediafile
import re
import sys
import copy
from typing import List
from modules.models.mediafile import MediaFile

try:
    import fcntl
    DEVNULL = '/dev/null'
except:
    DEVNULL = 'nul'
    pass


ACCEPTABLE_MEDIA_FILE_EXTENSIONS = {
    'm2ts', 'm2v',  'mov',  'mkv',  'mp4',  'mpeg', 'mpg',  'mpv',
    'mts',  'mxf',  'webm', 'ogg',  'gp3',  'avi',  'vob',  'ts',
    '264',  'h264',
    'flv',  'f4v',  'wav',  'ac3',  'aac',  'mp2',  'mp3',  'mpa',
    'sox',  'dts',  'dtshd'
}
SUPPORTED_STREAM_TYPES = {'video', 'audio', 'subtitles'}


class Inputs:

    class Streams:
        class Stream:
            def __init__(self, input_index, stream_type, stream_type_index, channels=1):
                self.input_index = input_index
                self.stream_type = stream_type
                self.stream_type_index = stream_type_index
                self.channels = channels

        def __init__(self):
            self.audio: List[self.Stream] = []
            self.video: List[self.Stream] = []
            self.subtitles: List[self.Stream] = []

        def append(self, stream):
            # if getattr(self, stream.stream_type) is None:
            #    setattr(self, stream.stream_type, [])
            getattr(self, stream.stream_type).append(stream)

        def append_files(self, files):
            for input_index, mediafile in enumerate(files):
                for stream_type_index, track in enumerate(mediafile.videoTracks):
                    self.append(self.Stream(input_index, 'video', stream_type_index))
                for stream_type_index, track in enumerate(mediafile.audioTracks):
                    self.append(self.Stream(input_index, 'audio', stream_type_index, track.channels))
                for stream_type_index, track in enumerate(mediafile.subTracks):
                    self.append(self.Stream(input_index, 'subtitles', stream_type_index))

        def remove_audio_input(self, ii):
            """
            Use this function to remove reference to extracted audio stream from AV file
            :param ii: extracted audio file's input_index
            :return:
            """
            i = len(self.audio)
            while i > 0:
                i -= 1
                if self.audio[i].input_index == ii:
                    self.audio.pop(i)

    def __init__(self, inputs):
        # ------------------------------------ #
        # Collect inputs
        # ------------------------------------ #
        self.files: List[MediaFile] = []
        for inp in inputs:
            try:
                ext = inp.rsplit('.', 1)[1]
                if ext in ACCEPTABLE_MEDIA_FILE_EXTENSIONS:
                    Logger.info('Appending input {0} ({1})\n'.format(inp, ext))
                    self.files.append(combined_info_mediafile(inp))
            except Exception as e:
                Logger.warning('Warning (files): {0} has no extension\n{1}\n'.format(input, e))
        self.streams = self.Streams()
        self.streams.append_files(self.files)

    def create_audio_previews_mono(self, asset_guid):
        procs = []
        # create extract processes
        output_dir = os.path.join(CONFIG_ANP['paths']['http_access_internal'], asset_guid)
        extern_dir = CONFIG_ANP['paths']['http_access_external']
        try: os.makedirs(output_dir)
        except: pass
        for ii, info in enumerate(self.infos):
            if 'video' in info or 'audio' not in info:
                continue
            filename = info['format']['ffprobe']['filename']
            command = [CONFIG_ANP['tools']['ffmpeg'], '-y', '-loglevel', 'error', '-i', filename]
            for ti, info_a in enumerate(info['audio']):
                channels = []
                ati = info_a['ffprobe']['index']
                for aci in range(info_a['ffprobe']['channels']):
                    sample = 'f{0:02d}_t{1:02d}_c{2:02d}.mp4'.format(ii, ati, aci)
                    channels.append('/'.join([extern_dir, asset_guid, sample]))
                    command += [
                        '-map', '0:{0}'.format(ati),
                        '-map_channel', '0.{0}.{1}'.format(ati, aci),
                        '-c:a', 'aac', '-strict', '-2', '-b:a', '64k',
                        os.path.join(output_dir, sample)
                    ]
                self.infos[ii]['audio'][ti]['preview'] = channels
            print utils.ffmpeg_format_command(command)
            procs.append(subprocess.Popen(command, stdout=0, stderr=0))
        for proc in procs:
            proc.wait()

    def create_audio_previews_mono_complex(self, asset_guid):
        procs = []
        # create extract processes
        output_dir = os.path.join(CONFIG_ANP['paths']['http_access_internal'], asset_guid)
        extern_dir = CONFIG_ANP['paths']['http_access_external']
        try: os.makedirs(output_dir)
        except: pass
        for ii, info in enumerate(self.infos):
            if 'video' in info or 'audio' not in info:
                continue
            filename = info['format']['ffprobe']['filename']
            for ti, info_a in enumerate(info['audio']):
                channels = []
                ati = info_a['ffprobe']['index']
                for aci in range(info_a['ffprobe']['channels']):
                    sample = 'f{0:02d}_t{1:02d}_c{2:02d}.mp4'.format(ii, ati, aci)
                    channels.append('/'.join([extern_dir, asset_guid, sample]))
                    command = [
                        CONFIG_ANP['tools']['ffmpeg'], '-y', '-loglevel', 'error', '-i', filename,
                        '-filter_complex', 'join=inputs={0}:channel_layout=mono:map={1}.{2}-FC'
                                           ''.format(len(info['audio']), ati, aci),
                        '-c:a', 'aac', '-strict', '-2', '-b:a', '64k',
                        os.path.join(output_dir, sample)
                    ]
                    print utils.ffmpeg_format_command(command)
                    procs.append(subprocess.Popen(command, stdout=0, stderr=0))
                self.infos[ii]['audio'][ti]['preview'] = channels
        for proc in procs:
            proc.wait()

    def create_audio_previews(self, output_dir, output_name):
        procs = []
        # create extract processes
        try: os.makedirs(output_dir)
        except: pass
        for ii, info in enumerate(self.infos):
            if 'video' in info or 'audio' not in info:
                continue
            suffix = ''
            filename = info['format']['ffprobe']['filename']
            command = [CONFIG_ANP['tools']['ffmpeg'], '-y', '-loglevel', 'error', '-i', filename, '-c:a', 'aac', '-strict', '-2']
            for j, info_a in enumerate(info['audio']):
                command += [
                    '-map', '0:{0}'.format(info_a['ffprobe']['index']),
                    '-b:a:{0}'.format(j), '{0}k'.format(60*info_a['ffprobe']['channels'])
                ]
                suffix += '_{0}c'.format(info_a['ffprobe']['channels'])
            sample = '{0}_{1:02d}{2}.mp4'.format(output_name, ii, suffix)
            command += [os.path.join(output_dir, sample)]
            print utils.ffmpeg_format_command(command)
            procs.append(subprocess.Popen(command, stdout=0, stderr=0))
        for proc in procs:
            proc.wait()

    def audio_stats(self):
        # Run this in separate thread
        # ,silencedetect=n=-60db
        threads = []
        for note in self.notes.audio:
            ii = note.input_index
            src = self.infos[ii]['format']['ffprobe']['filename']
            map = '0:{0}'.format(note.stream_type)
            command = [utils.FFMPEG, '-y', '-i', src, '-map', map, '-af', 'astats=length=1.0', '-acodec', 'pcm_s32le', '-f', 'null', 'nul']

    def scan_create_reference_extract_audio(self, dir_transit, dir_preview):
        # Create preview video and extract audio [and subtitles] tracks
        # audio_dir = os.path.join(dir_transit)
        # output_dir = os.path.join(CONFIG_ANP['paths']['http_access_internal'], asset_guid)
        # extern_dir = CONFIG_ANP['paths']['http_access_external']
        result = []
        extract_audio = []
        Logger.info('Create preview\n')
        for stream in self.streams.video:
            ii = stream.input_index
            scan_audio = []
            # Extract audio tracks from AV
            for sti, track in enumerate(self.files[ii].audioTracks):
                new_ii = len(self.files)
                # Mark track as extracted
                track.extracted = new_ii
                # Append audio stream
                self.streams.append(self.Streams.Stream(new_ii, 'audio', 0, track.channels))
                audio_transit = os.path.join(dir_transit, '{0}.{1}.{2}.mkv'.format(self.files[ii].guid, ii, track.index))
                extract_audio += ['-map', '0:a:{}'.format(sti), '-c:a', 'copy', audio_transit]
                scan_audio.append(audio_transit)
                # Create extracted mediafile
                amf = MediaFile()
                amf.audioTracks.append(track)
                amf.source.url = audio_transit
                self.files.append(amf)
            sample = '{0:02d}.{1:02d}.mp4'.format(ii, stream.stream_type_index)
            # Create video preview mediafile
            # video_preview = MediaFile()
            # video_preview.guid.new()
            # video_preview.master.set(self.files[ii].guid.guid)
            video_preview = self.files[ii].videoTracks[stream.stream_type_index].ref_add()
            cref = utils.ffmpeg_create_reference_extract_audio_subtitles(
                self.infos[ii],
                vnote.type_index,
                os.path.join(output_dir, sample),
                extract_audio
            )
            # Build cue map using blackdetect and silencedetect
            cuemap = []
            for bd in cref['blacks']:
                cuemap += [[bd[0], -1], [bd[1], 1]]
            # Scan embedded audio
            flag = 1
            if len(scan_audio):
                scan_audio_results = utils.ffmpeg_scan_audio(scan_audio, -55, 1.0)
                pprint.pprint(scan_audio_results)
                # Append silence info to blacks
                for res in scan_audio_results:
                    for sd in res['silencedetect']:
                        if len(sd) < 2:
                            sd += [50000.0, 50000.0]
                        cuemap += [[sd[0], -1], [sd[1], 1]]
                cuemap.sort()
                flag += len(scan_audio_results)
            # Merge blacks and silence
            newmap = []
            black_silence_start = 0.0
            for cue in cuemap:
                flag += cue[1]
                if flag == 0:
                    # start of black+silence
                    black_silence_start = cue[0]
                elif flag == 1 and cue[1] == 1:
                    # end of black+silence
                    newmap.append([black_silence_start, cue[0]])
            print 'Merged blackdetect & silencedetect:'
            pprint.pprint(newmap)
            # guess in/out points
            # suppose that in-point should be in first half of media file, and in first 200 seconds
            program_in = 0.0
            program_out = self.infos[ii]['video'][vnote.type_index]['override']['duration']
            bound_in = min(program_out / 2.0, 200.0)
            bound_out = program_out / 2.0
            for black in newmap:
                if black[1] <= bound_in:
                    program_in = math.floor(black[1])
                elif black[0] >= bound_out:
                    program_out = black[0]
            crop = {'x': 65535, 'y': 65535, 'w': 0, 'h': 0}
            for c2 in cref['crops']:
                if program_in <= c2['pts_time'] <= program_out:
                    utils.crop_update(crop, c2['crop'])
            if crop['x'] == 65535:
                crop = {
                    'x': 0,
                    'y': 0,
                    'w': self.infos[ii]['video'][vnote.type_index]['ffprobe']['width'],
                    'h': self.infos[ii]['video'][vnote.type_index]['ffprobe']['height']
                }
            cref.update({'black_silence_map': newmap, 'program_in': program_in, 'program_out': program_out, 'crop': crop})
            result.append(cref)
            self.notes.remove_audio_input(ii)
            self.audio_pairs.remove_input(ii)
        # Scan audio
        print self.notes.audio
        print 'SCAN FINISHED'
        return result

    def __unicode__(self):
        string = ''
        string += 'Infos:\n'
        for info in self.infos:
            string += pprint.pformat(info) + '\n'
        string += 'Notes:\n{0}\nAudio pairs:\n{1}\n'.format(self.notes, self.audio_pairs)
        return string

    def __repr__(self):
        return self.__unicode__()


class Ingest:
    def __init__(self, dir_work, dir_done, dir_fail):
        self.dir_work = dir_work
        self.dir_done = dir_done
        self.dir_fail = dir_fail
        inputs = []
        for root, firs, files in os.walk(dir_work):
            inputs += [os.path.join(root, f) for f in files]
        self.inputs = Inputs(inputs)

    def create_previews(self, dir_preview):



