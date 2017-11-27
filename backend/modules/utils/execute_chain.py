# -*- coding: utf-8 -*-
# tim.lansen@gmail.com
# Chain execution area
# Chain is a list of processes connected with pipes
# Each process sends it's STDOUT to next process' STDIN
# The progress source process' STDERR is being parsed and sent to executor
# Every process' STDERR being read and stored

# Chain execution

import os
import re
import time
import uuid
from typing import List
from multiprocessing import Process, Event
from .cross_process_lossy_queue import CPLQueue

from subprocess import Popen, PIPE
from modules.models.job import Job
from modules.models.node import Node
from modules.models.asset import Asset
from modules.models.mediafile import MediaFile
from modules.config.trix_config import TrixConfig
from .log_console import Logger, tracer
from .combined_info import combined_info, combined_info_mediafile
from .commands import *
from .pipe_nowait import pipe_nowait
from .parsers import PARSERS
from .ffmpeg_utils import ffmpeg_create_preview_extract_audio_subtitles, mediafile_asset_for_ingest, ffmpeg_get_iframes
from .mp4box_utils import mp4box_concat
from .slices import create_slices
from .storage import Storage
from .exchange import Exchange

from .database import DBInterface


# def _icpeas(mf: MediaFile, ass: str, out_progress: CPLQueue, out_final: CPLQueue):
#     tdir = Storage.storage_path('transit', str(mf.guid))
#     pdir = Storage.storage_path('preview', str(mf.guid))
#     data = ffmpeg_create_preview_extract_audio_subtitles(mf, tdir, pdir, out_progress)
#     data['asset'].name = 'auto'
#     data['asset'].guid.set(ass)
#     # Logger.critical('{}\n'.format(data))
#     out_final.put([data])


class ExecuteInternal:
    class combined_info:
        REQUIREMENTS = TrixConfig.Nodes.Role.INFO

        @staticmethod
        def handler(params, out_progress: CPLQueue, out_final: CPLQueue):
            """
            Compose ffprobe and mediainfo
            :param params:            ['<predefined>', '<url>']
            :param out_progress:      progress output queue
            :param out_final:         final output queue
            :param chain_error_event: error event
            :return:
            """
            mf: MediaFile = MediaFile()
            mf.update_str(params[0])
            combined_info(mf, params[1])
            Logger.debug('{}\n...\n'.format(mf.dumps(indent=2)[:250]), Logger.LogLevel.LOG_CRIT)
            out_final.put([mf])

    class create_mediafile_and_asset:
        REQUIREMENTS = TrixConfig.Nodes.Role.INFO

        @staticmethod
        def handler(params, out_progress: CPLQueue, out_final: CPLQueue):
            """
            Get combined info, create mediafile and asset
            :param params:            ['<url>', '<task id>']
            :param out_progress:      progress output queue
            :param out_final:         final output queue
            :param chain_error_event: error event
            :return:
            """
            # adir = Storage.storage_path('archive', None)
            # tdir = Storage.storage_path('transit', None)
            # pdir = Storage.storage_path('preview', None)
            res = mediafile_asset_for_ingest(params[0])
            if type(res) is dict:
                res['asset'].taskId.set(params[1])
            out_final.put([res])

    class create_slices:
        REQUIREMENTS = TrixConfig.Nodes.Role.VIDEO_SLICER

        @staticmethod
        def handler(params, out_progress: CPLQueue, out_final: CPLQueue):
            """
            Prepare media for ingest
            :param params:            ['<mediaFile.dumps()>', <vti>]
            :param out_progress:      progress output queue
            :param out_final:         final output queue
            :param chain_error_event: error event
            :return: mediaFile + set of data to create jobs for sliced transcode and A/S extraction
            """
            # mf: MediaFile = MediaFile(guid=None)
            # mf.update_str(params[0])
            mf: MediaFile = DBInterface.MediaFile.get(params[0])
            slices = create_slices(mf, params[1])
            Logger.info('ExecuteInternal.create_slices.handler: slices\n{}\n'.format(slices))
            out_final.put([slices])

    class extract_audio_subtitles_create_slices:
        @staticmethod
        def handler(params, out_progress: CPLQueue, out_final: CPLQueue):
            pass

    class create_preview_extract_audio_subtitles:
        REQUIREMENTS = TrixConfig.Nodes.Role.AV_ENCODER

        @staticmethod
        def handler(params, out_progress: CPLQueue, out_final: CPLQueue):
            """
            Prepare media for ingest
            :param params:            ['<url>', '<asset guid>', '<task guid>']
            :param out_progress:      progress output queue
            :param out_final:         final output queue
            :param chain_error_event: error event
            :return:
            """
            mf = combined_info_mediafile(params[0])
            # _icpeas(mf, params[1], out_progress, out_final)
            asset_guid = params[1]
            task_guid = params[2]
            tdir = Storage.storage_path('transit', str(mf.guid))
            pdir = Storage.storage_path('preview', str(mf.guid))
            data = ffmpeg_create_preview_extract_audio_subtitles(mf, tdir, pdir, out_progress)
            data['asset'].name = 'auto'
            data['asset'].guid.set(asset_guid)
            data['asset'].taskId.set(task_guid)
            out_final.put([data])

    class asset_to_mediafile:
        REQUIREMENTS = TrixConfig.Nodes.Role.VIDEO_ENCODER_SLICED | TrixConfig.Nodes.Role.INFO

        @staticmethod
        def handler(params, out_progress: CPLQueue, out_final: CPLQueue):
            """
            Create mediafile using asset
            :param params:       [<expanded asset>]
            :param out_progress: progress output queue
            :param out_final:    final output queue (mediaFile)
            :return:
            """

            reencode = False

            asset: Asset = Exchange.object_decode(params[0])
            vstr: Asset.VideoStream = asset.videoStreams[0]
            media_files_dict = {}
            for mf in asset.mediaFiles + asset.mediaFilesExtra:
                media_files_dict[str(mf.guid)] = mf

            # TODO take into account the rate conversion

            tmpdir = '/mnt/server2_id/cache/{}'.format(asset.guid)
            os.makedirs(tmpdir, exist_ok=True)

            mediafile: MediaFile = MediaFile(name='Made from asset')
            adir = Storage.storage_path('archive', str(mediafile.guid))
            path = '{}/{}.mp4'.format(adir.sub_path, mediafile.guid)
            os.makedirs(adir.sub_path, exist_ok=True)

            # Trim source video if needed
            # Search mediafile that contains video
            mf_video: MediaFile = None
            for mf in asset.mediaFiles:
                if len(mf.videoTracks):
                    mf_video = mf
                    break
            pre_archive_id = str(mf_video.videoTracks[0].archive)
            if pre_archive_id in media_files_dict:
                mf_video = media_files_dict[pre_archive_id]
            video_src = mf_video.source.path
            video_stream = asset.videoStreams[0]
            scale_time_fps = video_stream.fpsOriginal.val() / video_stream.fpsEncode.val()
            tempo_fps = video_stream.fpsEncode.val() / video_stream.fpsOriginal.val()
            program_in = scale_time_fps * video_stream.program_in
            program_out = scale_time_fps * video_stream.program_out
            if program_in is None or program_in < 0.2:
                program_in = 0.0
            elif not reencode:
                start = max(0.0, program_in - 1.0)
                iscan = ffmpeg_get_iframes(video_src, start)
                tp = None
                pin = None
                for scan in iscan:
                    t = start + float(scan['pts_time'])
                    if t >= program_in:
                        if tp is None or t - program_in <= 0.2:
                            pin = t
                            break
                        pin = tp
                        break
                    tp = t
                if pin is None:
                    pin = tp
                program_in = pin
                video_stream.program_in = program_in * tempo_fps
            if program_out is None or abs(mf_video.format.duration - program_out) < 0.2:
                program_out = mf_video.format.duration
            elif not reencode:
                start = program_out - 1.0
                iscan = ffmpeg_get_iframes(video_src, start)
                tp = None
                pout = None
                for scan in iscan:
                    t = start + float(scan['pts_time'])
                    if t >= program_in:
                        pout = t
                        break
                    tp = t
                if pout is None:
                    pout = tp
                program_out = pout
                video_stream.program_out = program_out * tempo_fps

            program_dur = program_out - program_in
            trimmed_video_file = '{}/video.mp4'.format(tmpdir)
            if reencode:
                # if vstr.cropdetect.w is None:
                if program_in > 5:
                    ss0 = int(program_in - 3.0)
                    ss1 = program_in - ss0
                    command = 'ffmpeg -y -loglevel error -stats -ss {ss0} -i {src} -ss {ss1:.6f} -map v:0 -t {dur} -c:v libx264 -b:v 6000k {dst}'.format(
                        ss0=ss0, ss1=ss1,
                        dur=program_dur,
                        src=video_src,
                        dst=trimmed_video_file,
                    )
                elif program_in > 0.0:
                    command = 'ffmpeg -y -loglevel error -stats -i {src} -ss {ss1:.6f} -map v:0 -t {dur} -c:v libx264 -b:v 6000k {dst}'.format(
                        ss1=program_in,
                        dur=program_dur,
                        src=video_src,
                        dst=trimmed_video_file,
                    )
                else:
                    command = 'ffmpeg -y -loglevel error -stats -i {src} -map v:0 -t {dur} -c:v libx264 -b:v 6000k {dst}'.format(
                        dur=program_dur,
                        src=video_src,
                        dst=trimmed_video_file,
                    )
                # else:
                #     command = 'ffmpeg -y -loglevel error -stats -ss {start} -i {src} -map v:0 -t {dur} -c:v libx264 -b:v 6000k -vf {vf} {dst}'.format(
                #         start=program_in,
                #         dur=program_dur,
                #         src=video_src,
                #         dst=trimmed_video_file,
                #         vf=vstr.cropdetect.filter_string()
                #     )
                Logger.log('{}\n'.format(command), Logger.LogLevel.LOG_WARNING)
                proc = Popen(command.split(' '))
                proc.communicate()
                # TODO check proc.returncode
            else:
                if abs(asset.mediaFiles[asset.videoStreams[0].channels[0].src_stream_index].format.duration - program_out) < 0.2:
                    trimmed_video_file = video_src
                else:
                    command = 'ffmpeg -y -loglevel error -stats -ss {start} -i {src} -t {dur} -c copy {dst}'.format(
                        start=program_in,
                        dur=program_dur,
                        src=video_src,
                        dst=trimmed_video_file
                    )
                    Logger.log('{}\n'.format(command), Logger.LogLevel.LOG_WARNING)
                    proc = Popen(command.split(' '))
                    proc.communicate()
                    # TODO check proc.returncode

            def mfindex(atindex):
                for i, mf in enumerate(asset.mediaFiles):
                    if atindex < len(mf.audioTracks):
                        return [i, i, atindex]
                    atindex -= len(mf.audioTracks)
                return None

            # cdir = Storage.storage_path('cache', str(asset.guid))

            # FIXME calculate start/duration for every track
            # commands = []
            audio_files = []

            # Compile audio tracks
            for i, audio_stream in enumerate(asset.audioStreams):
                output = '{}/{}.mp4'.format(tmpdir, str(uuid.uuid4()))
                audio_files.append(output)
                command = 'ffmpeg -y -loglevel error -stats'
                # Calculate start, duration and rate
                if audio_stream.sync.delay1 is None:
                    audio_in = video_stream.program_in
                    audio_out = video_stream.program_out
                    sync_tempo_encoded = tempo_fps
                elif audio_stream.sync.delay2 is None:
                    audio_in = video_stream.program_in + audio_stream.sync.delay1
                    audio_out = video_stream.program_out + audio_stream.sync.delay1
                    sync_tempo_encoded = tempo_fps
                else:
                    a1 = audio_stream.sync.offset1
                    a2 = audio_stream.sync.offset2
                    v1 = a1 + audio_stream.sync.delay1
                    v2 = a2 + audio_stream.sync.delay2

                    sync_tempo_original = (a2 - a1) / (v2 - v1)
                    audio_in = a2 - (v2 - video_stream.program_in) * sync_tempo_original
                    audio_out = a1 + (video_stream.program_out - v1) * sync_tempo_original
                    sync_tempo_encoded = sync_tempo_original * tempo_fps

                audio_dur = audio_out - audio_in

                # Filter source media files
                source_mediafiles_streams = [mfindex(ch.src_stream_index) + [ch.src_channel_index] for ch in audio_stream.channels]
                smss = sorted(list(set([_[0] for _ in source_mediafiles_streams])))
                offsets = []
                idx = 0
                for mfi in smss:
                    if mfi > idx:
                        offsets.append([mfi, mfi - idx])
                    idx = mfi + 1
                for off in offsets:
                    for idx in range(len(source_mediafiles_streams)):
                        if source_mediafiles_streams[idx][0] >= off[0]:
                            source_mediafiles_streams[idx][0] -= off[1]
                # Debug
                # Logger.warning('\n{}\n'.format(audio_stream))
                # Logger.error('{}\n'.format(source_mediafiles_streams))
                # Collect source files
                join_inputs = 0
                joined = set([])
                for smfs in source_mediafiles_streams:
                    if smfs[1] not in joined:
                        joined.add(smfs[1])
                        mf: MediaFile = asset.mediaFiles[smfs[1]]
                        # TODO optimize extracted tracks usage
                        if mf.audioTracks[0].extract is None:
                            join_inputs += len(mf.audioTracks)
                            command += ' -ss {start} -i {src}'.format(start=audio_in, src=mf.source.path)
                        else:
                            for at in mf.audioTracks:
                                mfe: MediaFile = media_files_dict[str(at.extract)]
                                join_inputs += 1
                                command += ' -ss {start} -i {src}'.format(start=audio_in, src=mfe.source.path)
                command += ' -t {:.3f}'.format(audio_dur)
                # Compose filter, example:
                # join=inputs=2:channel_layout=5.1:map=0.0-FL|0.1-FR|1.2-FC|1.3-LFE|1.1-BL|0.5-BR
                layout = Asset.AudioStream.Layout.LAYMAP[audio_stream.layout]
                layout_dst = layout['layout']
                layout_map = '|'.join(['{}.{}-{}'.format(_s[2], _s[3], layout_dst[_i]) for _i, _s in enumerate(source_mediafiles_streams)])
                command += ' -filter_complex join=inputs={inputs}:channel_layout={layout}:map={laymap}'.format(
                    inputs=join_inputs,
                    layout=audio_stream.layout,
                    laymap=layout_map
                )
                if abs(sync_tempo_encoded - 1.0) > 0.00001:
                    command += ',atempo={:.8f}'.format(sync_tempo_encoded)
                bitrate = 96 * len(audio_stream.channels)
                command += ' -c:a aac -strict -2 -b:a {br}k -metadata:s:a:0 language={lang} {dst}'.format(
                    br=bitrate,
                    lang=audio_stream.language,
                    dst=output
                )
                Logger.log('{}\n'.format(command), Logger.LogLevel.LOG_WARNING)
                proc = Popen(command.split(' '))
                proc.communicate()
                # TODO check proc.returncode

            # Assemble video and audio
            command = 'ffmpeg -y -loglevel error -stats -i {video} {audio} {smap} -c copy {dst}'.format(
                video=trimmed_video_file,
                audio=' '.join(['-i {}'.format(_) for _ in audio_files]),
                smap='-map 0:v {}'.format(' '.join(['-map {}:a'.format(_i + 1) for _i in range(len(audio_files))])),
                dst=path
            )
            Logger.log('{}\n'.format(command), Logger.LogLevel.LOG_WARNING)
            proc = Popen(command.split(' '))
            proc.communicate()
            # TODO check proc.returncode

            combined_info(mediafile)
            out_final.put([Exchange.object_encode(mediafile)])

    class mp4box_concat_update_mediafile:
        REQUIREMENTS = TrixConfig.Nodes.Role.CONCATENATOR

        @staticmethod
        def handler(params, out_progress: CPLQueue, out_final: CPLQueue):
            """
            Assemble mediafile from video segments [and audio tracks]
            :param params:            ['<predefined>', '<output url>', '<mp4box params>', [<video segments>], [<audio tracks>]]
            :param out_progress:      progress output queue
            :param out_final:         final output queue: [mediaFile]
            :param chain_error_event: error event
            :return:
            """
            rc = mp4box_concat(params[1], params[2], params[3], params[4])
            mf = None
            dirs = set([])
            if rc == 0:
                for path in params[3]:
                    dirs.add(os.path.dirname(path))
                    os.remove(path)
                for d in dirs:
                    try:
                        Logger.debug('Removing directory {}\n'.format(d), Logger.LogLevel.LOG_INFO)
                        os.rmdir(d)
                    except:
                        Logger.warning('Failed to remove directory {}\n'.format(d))
                        pass
                mf: MediaFile = MediaFile()
                mf.update_str(params[0])
                combined_info(mf, params[1])
            out_final.put([mf])

    class remove_files:
        @staticmethod
        def handler(params, out_progress: CPLQueue, out_final: CPLQueue):
            """
            Remove files and directories
            :param params:            ['<file1>', '<file2>', ...]
            :param out_progress:      progress output queue
            :param out_final:         final output queue
            :param chain_error_event: error event
            :return:
            """
            dirs = set([])
            for path in params:
                dirs.add(os.path.dirname(path))
                os.remove(path)
            for d in dirs:
                try:
                    Logger.debug('Removing directory {}\n'.format(d), Logger.LogLevel.LOG_INFO)
                    os.rmdir(d)
                except:
                    Logger.warning('Failed to remove directory {}\n'.format(d))
                    pass
            out_final.put(list(dirs))

# def internal_ingest_assets(params, out_progress: CPLQueue, out_final: CPLQueue):
#     """
#     Create interaction request from list of assets
#     :param params: [<pickle(['guid', 'guid', ...])>]
#     :param out_progress:
#     :param out_final:
#     :return:
#     """
#     # List of asset.guid
#     asset_guids = pickle.loads(base64.b64decode(params[0]))
#     Logger.critical('internal_ingest_assets: {}\n'.format(asset_guids))
#     # Request assets from DB
#     assets =


def execute_internal(params: List[str],
                     out_progress: CPLQueue,
                     out_final: CPLQueue,
                     chain_error_event: Event):
    """
    Execute internal (complex) procedure, pass progress if able to, and pass final results
    :param params:            ['<procedure>', '<param1>', '<param2>', ...]
    :param out_progress:      progress output queue
    :param out_final:         final output queue
    :param chain_error_event: error event
    :return:
    """
    try:
        pname = params[0].split('.', 1)[1]
        proc = ExecuteInternal.__dict__[pname].handler
        proc(params[1:], out_progress, out_final)
    except Exception as e:
        Logger.error('execute_internal failed: {}\n'.format(e))
        Logger.traceback(Logger.LogLevel.LOG_ERR)
        # for frame in traceback.extract_tb(sys.exc_info()[2]):
        #     print(frame)
        chain_error_event.set()
    Logger.log('execute_internal finished\n')


# Execute chain object
# Chain description may be found in modules.models.job
# In short: Chain is a list of processes that being started simultaneously and compiled into a chain,
# where STDOUT of every process is attached to STDIN of next process
def execute_chain(chain: Job.Info.Step.Chain,
                  out_progress: CPLQueue,
                  out_result: CPLQueue,
                  chain_enter_event: Event,
                  chain_error_event: Event,
                  chain_finish_event: Event,
                  output_is_read: Event):
    chain_enter_event.set()
    if chain_error_event.is_set():
        Logger.debug('Error event is already set\n', Logger.LogLevel.LOG_ERR)
        return
    # Handle special complex cases
    if len(chain.procs) == 1 and chain.procs[0][0].startswith('ExecuteInternal.'):
        execute_internal(chain.procs[0], out_progress, out_result, chain_error_event)
        chain_finish_event.set()
        return
    if chain.return_codes is None or len(chain.procs) != len(chain.return_codes):
        Logger.error('Chain must have {} return_codes list(s)\n'.format(len(chain.procs)))
        chain_error_event.set()
        return
    proc = []
    text = ['' for _ in chain.procs]
    stderr_handles = []
    pstdout = PIPE
    Logger.log('{0}\n'.format(' \\\n|'.join([format_command(_) for _ in chain.procs])))
    for i, c in enumerate(chain.procs):
        try:
            p = Popen(c, stdin=pstdout, stdout=PIPE, stderr=PIPE)
        except Exception as e:
            Logger.error('Failed to launch {}\n'.format(c[0]))
            Logger.error('{}\n'.format(e))
            # Stop procs that already launched
            while i > 0:
                i -= 1
                Logger.debug('Stopping proc #{0}\n'.format(i), Logger.LogLevel.LOG_WARNING)
                proc[i].kill()
                proc[i].wait()
            chain_error_event.set()
            return
        pipe_nowait(p.stderr)
        proc.append(p)
        pstdout = p.stdout
        stderr_handles.append(p.stderr.fileno())
    for p in proc:
        p.stdout.close()
    all_completed = False
    progress_parser = PARSERS[chain.progress.parser] if chain.progress.parser in PARSERS else lambda x: None
    feeds = re.compile(b'[\\r\\n]+')
    while not all_completed:
        all_completed = True
        if chain_error_event.is_set():
            for i, p in enumerate(proc):
                if p is not None:
                    Logger.debug('Stopping proc #{0}\n'.format(i), Logger.LogLevel.LOG_WARNING)
                    p.kill()
                    p.wait()
                proc[i] = None
            break
        for i, p in enumerate(proc):
            # Skip finished process
            if p is None:
                continue
            s = stderr_handles[i]
            try:
                part = feeds.sub(b'\n', os.read(s, 65536)).decode()
                text[i] += part
                line = part.strip().rsplit('\n', 1)[-1]
                if i == chain.progress.capture and len(line):
                    cap = progress_parser(line)
                    if cap:
                        if 'time' in cap:
                            out_progress.put(cap)
                # if i == 0:
                #     Logger.warning('{}\n'.format(part))
            except OSError as e:
                pass

            if p.poll() is None:
                all_completed = False
            else:
                # Check retcode
                rc = p.returncode
                if chain.return_codes[i] is None:
                    Logger.debug('Ignoring return code {} from process #{}\n'.format(rc, i), Logger.LogLevel.LOG_WARNING)
                elif rc not in chain.return_codes[i]:
                    # Error, stop chain
                    Logger.debug('Bad retcode in op#{0}: {1}\n'.format(i, rc), Logger.LogLevel.LOG_ERR)
                    chain_error_event.set()
                proc[i] = None
        time.sleep(0.4)
    # Collect ALL outputs
    # TODO: filter out progress lines
    out_result.put(text)
    Logger.debug('Chain finished\n', Logger.LogLevel.LOG_INFO)
    chain_finish_event.set()
    output_is_read.wait(timeout=5)
    # for i, t in enumerate(text):
    #     sys.stderr.write('\x1b[0;1;{0}m{1}\n\x1b[0m'.format(29 + i, t))
    # print('Execute chain finished')


def test():
    test_chain_enter = Event()
    test_chain_error = Event()

    test_chain = Job.Info.Step.Chain()
    test_chain.return_codes = [[0], [0]]

    # test_chain.procs = [
    #     "ffmpeg -y -loglevel error -stats -i F:\Kinozal\Der.gezaehmte.Widerspenstige.1980.720p.BluRay.mkv -t 60 -map v:0 -c:v libx264 -b:v 1000k -preset slow -g 50 -refs 2 -f mp4 nul".split(' ')
    # ]
    # test_chain.progress.capture = 0
    test_chain.procs = [
        r"ffmpeg -y -loglevel error -stats -i /mnt/server1_id/crude/in_work/test_eng1_20.mp4 -t 90 -map a:0 -c:a pcm_s32le -f sox -".split(' '),
        r"sox -t sox - -t sox - remix 1v0.5,2v0.5 sinc -p 10 -t 5 100-3500 -t 10".split(' '),
        r"ffmpeg -y -loglevel error -stats -f sox -i - -c:a aac -b:a 128k -strict -2 /mnt/server1_id/crude/in_work/test_eng1_20.chain.mp4".split(' ')
    ]
    test_chain.progress.capture = 2

    test_chain.progress.parser = 'ffmpeg'

    test_output: List[CPLQueue] = [CPLQueue(5) for _ in test_chain.procs]

    # Multi-capture chain
    test_process = Process(target=execute_chain, args=(test_chain, test_output, test_chain_enter, test_chain_error))
    test_process.start()

    test_chain_enter.wait()
    test_chain_enter.clear()

    def dummy_parser(c):
        Logger.debug('DUMMY PARSER: {}\n'.format(str(c)[:250]), Logger.LogLevel.LOG_WARNING)
        return None

    parser = dummy_parser if test_chain.progress.parser is None or test_chain.progress.parser not in PARSERS else PARSERS[test_chain.progress.parser]

    while True:
        if not test_process.is_alive():
            break
        # Compile info from chains
        for j, q in enumerate(test_output):
            c = q.flush()
            if c and j == test_chain.progress.capture:
                parsed = parser(c)
                Logger.debug('{}\n'.format(parsed), Logger.LogLevel.LOG_INFO)
            time.sleep(0.1)

    Logger.debug('Done\n', Logger.LogLevel.LOG_CRIT)

