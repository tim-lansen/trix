# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import re
import os
import json
import uuid
import copy
import math
from pprint import pformat
from typing import List
from modules.models.job import Job, Task
from modules.models.asset import Asset, Stream
from modules.models.mediafile import MediaFile
from modules.models.interaction import Interaction
from modules.utils.database import DBInterface
from .log_console import Logger, tracer
from .storage import Storage
from .parsers import astats_to_model, Parsers
from .types import Guid, Rational
from modules.models.collector import Collector
from .exchange import Exchange


# def fps2int(fps: Rational):
#     fps.sanitize(math.floor(fps.val() + 0.5), 1)
#     fi = fps.__class__([math.floor(fps.val() + 0.5), 1])
#     return fi


def merge_assets(assets):
    # def _advance_stream(_s: Stream, _i):
    #     for _ch in _s.channels:
    #         _ch.src_stream_index += _i

    def _advance_streams(_class, _ss: List[dict], _i):
        _ass = []
        if _ss is not None and len(_ss) > 0:
            for _s in _ss:
                for _ch in _s['channels']:
                    _ch['src_stream_index'] += _i
                _cs = _class()
                _cs.update_json(_s)
                _ass.append(_cs)
        return _ass

    asset: Asset = Asset(programName=', '.join([_.programName for _ in assets]))
    vii = 0
    aii = 0
    sii = 0
    Logger.log('merge_assets:\n\n')
    for a in assets:
        Logger.info('{}\n\n'.format(pformat(a)))

        vss = _advance_streams(Asset.VideoStream, a['videoStreams'], vii)
        vii += len(vss)
        ass = _advance_streams(Asset.AudioStream, a['audioStreams'], aii)
        aii += len(ass)
        sss = _advance_streams(Asset.SubStream, a['subStreams'], sii)
        sii += len(sss)

        Logger.log('vss: {}\nass: {}\n sss: {}\n\n'.format(vss, ass, sss))

        asset.videoStreams += vss
        asset.audioStreams += ass
        asset.subStreams += sss

        asset.mediaFiles += [Asset.MediaFile(_) for _ in a['mediaFiles']]
        if type(a['mediaFilesExtra']) is list:
            asset.mediaFilesExtra += [Asset.MediaFileExtra(_) for _ in a['mediaFilesExtra']]

    return asset


def merge_assets_create_interaction(asset_ids: List[str]):
    # Get assets from DB, merge and create Interaction
    guid = None
    if len(asset_ids) == 1:
        guid = asset_ids[0]
        asset = DBInterface.Asset.get(guid)
    elif len(asset_ids) > 1:
        assts = DBInterface.Asset.records(asset_ids)
        assm = {}
        for i, asst in enumerate(assts):
            assm[str(asst['guid'])] = i
        assets = [assts[assm[aid]] for aid in asset_ids]
        asset = merge_assets(assets)
        asset.name = 'merged'
        DBInterface.Asset.set(asset)
        guid = str(asset.guid)
    if guid:
        # Create Interaction
        inter = Interaction()
        inter.guid.new()
        inter.name = asset.programName
        inter.assetIn.set(guid)
        inter.assetOut = None
        DBInterface.Interaction.set(inter)
        guid = str(inter.guid)
    return guid


class JobUtils:
    TRIMMER = 'trim.out'

    ACCEPTABLE_MEDIA_FILE_EXTENSIONS = {
        'm2ts', 'm2v', 'mov', 'mkv', 'mp4', 'mpeg', 'mpg', 'mpv',
        'mts', 'mxf', 'webm', 'ogg', 'gp3', 'avi', 'vob', 'ts',
        '264', 'h264',
        'flv', 'f4v', 'wav', 'ac3', 'aac', 'mp2', 'mp3', 'mpa',
        'sox', 'dts', 'dtshd'
    }

    PIX_FMT_MAP_X265 = {
        'yuv420p':     {                    'd': 8, 'csp': 'i420', 'P': 'main',        'x265': 'x265.08', 'bs': 0.15},     # Bitrate scale = depth * csp / 640
        'yuv422p':     {                    'd': 8, 'csp': 'i422',                     'x265': 'x265.08', 'bs': 0.2},      # No standard profile for 8-bit 422
        'yuv420p10le': {                    'd': 10, 'csp': 'i420', 'P': 'main10',     'x265': 'x265.10', 'bs': 0.1875},
        'yuv422p10le': {                    'd': 10, 'csp': 'i422', 'P': 'main422-10', 'x265': 'x265.10', 'bs': 0.25},
        'yuv420p10be': {'t': 'yuv420p10le', 'd': 10, 'csp': 'i420', 'P': 'main10',     'x265': 'x265.10', 'bs': 0.1875},
        'yuv422p10be': {'t': 'yuv422p10le', 'd': 10, 'csp': 'i422', 'P': 'main422-10', 'x265': 'x265.10', 'bs': 0.25},
        'yuv420p12le': {                    'd': 12, 'csp': 'i420', 'P': 'main12',     'x265': 'x265.12', 'bs': 0.225},
        'yuv422p12le': {                    'd': 12, 'csp': 'i422', 'P': 'main422-12', 'x265': 'x265.12', 'bs': 0.3},
        'yuv420p12be': {'t': 'yuv420p12le', 'd': 12, 'csp': 'i420', 'P': 'main12',     'x265': 'x265.12', 'bs': 0.225},
        'yuv422p12be': {'t': 'yuv422p12le', 'd': 12, 'csp': 'i422', 'P': 'main422-12', 'x265': 'x265.12', 'bs': 0.3},
        'default':     {'t': 'yuv422p12le', 'd': 12, 'csp': 'i422', 'P': 'main422-12', 'x265': 'x265.12', 'bs': 0.3}
    }
    PIX_FMT_MAP_X264 = {
        'yuv420p':     {                    'd': 8, 'csp': 'i420', 'P': 'main',     'x264': 'x264.08', 'bs': 0.15},  # Bitrate scale = depth * csp / 640
        'yuv422p':     {                    'd': 8, 'csp': 'i422',                  'x264': 'x264.08', 'bs': 0.2},  # No standard profile for 8-bit 422
        'yuv420p10le': {                    'd': 10, 'csp': 'i420', 'P': 'high10',  'x264': 'x264.10', 'bs': 0.1875},
        'yuv422p10le': {                    'd': 10, 'csp': 'i422', 'P': 'high422', 'x264': 'x264.10', 'bs': 0.25},
        'yuv420p10be': {'t': 'yuv420p10le', 'd': 10, 'csp': 'i420', 'P': 'high10',  'x264': 'x264.10', 'bs': 0.1875},
        'yuv422p10be': {'t': 'yuv422p10le', 'd': 10, 'csp': 'i422', 'P': 'high422', 'x264': 'x264.10', 'bs': 0.25},
        'default':     {'t': 'yuv422p10le', 'd': 10, 'csp': 'i422', 'P': 'high422', 'x264': 'x264.10', 'bs': 0.3}
    }

    @staticmethod
    def calc_bitrate_x265_kbps(fmap, w, h, fps):
        br = 400 + int(0.001 * w * h * fps * fmap['bs'])
        br -= br % 10
        return br

    class CreateJob:
        @staticmethod
        def _media_info(inputs, group_id, names: List[str], output: dict):
            """
            Create a job that analyzes source(s) and creates MediaFile(s)
            :param inputs: list of files, path to file, or directory
            :param group_id: job group for depending job(s)
            :param names: strings that may help to identify media
            :param output: dict object {'job': None, 'mediafiles': []}
            :return: job or None
            """
            output['job'] = None
            output['mediafiles'] = []
            paths = []
            if type(inputs) is list:
                paths = inputs
            elif os.path.isfile(inputs):
                paths = [inputs]
            elif os.path.isdir(inputs):
                for root, firs, files in os.walk(inputs):
                    for f in files:
                        ne = f.rsplit('.', 1)
                        if len(ne) == 2 and ne[1] in JobUtils.ACCEPTABLE_MEDIA_FILE_EXTENSIONS:
                            paths.append(os.path.join(root, f))
                            names.append(ne[0])
            if len(paths) == 0:
                Logger.error('Cannot find file(s) in {}\n'.format(inputs))
                return None
            # Store common path to aliases as base
            base = os.path.commonpath((os.path.dirname(_) for _ in paths))
            # Create job
            job: Job = Job(name='Combined Info(s)', guid=0, task_id=0)
            job.type = Job.Type.PROBE
            job.info.names = names
            job.info.aliases['base'] = base
            if group_id is not None:
                job.groupIds.append(group_id)
            step: Job.Info.Step = Job.Info.Step()
            step.name = 'Get combined info(s)'
            job.info.steps.append(step)
            for ci, p in enumerate(paths):
                uidn = 'uid{:02d}'.format(ci)
                srcn = 'src{:02d}'.format(ci)
                # Set ailases
                mfid = str(uuid.uuid4())
                output['mediafiles'].append(mfid)
                job.info.aliases[srcn] = p.replace(base, '${base}', 1)
                job.info.aliases[uidn] = mfid
                # Compose chain
                chain = Job.Info.Step.Chain()
                chain.procs = [
                    ['ExecuteInternal.combined_info', '{{"guid":"${{{}}}"}}'.format(uidn), '${{{}}}'.format(srcn)]
                ]
                chain.result = 0
                # chain.return_codes = [[0, 1]]
                step.chains.append(chain)
                # Compose result that register new media file
                result = Job.Emitted.Result()
                result.handler = JobUtils.ResultHandlers.mediafile.__name__
                result.source.chain = ci
                job.emitted.results.append(result)
            output['job'] = job
            return str(job.guid)

        @staticmethod
        def _cpeas(path, asset_guid, task_id=0):
            job: Job = Job('CPEAS: {}'.format(os.path.basename(path)), 0, task_id)
            job.type = Job.Type.CPEAS
            step: Job.Info.Step = Job.Info.Step()
            step.name = 'Create proxy, extract audio and subtitles'
            job.info.steps.append(step)
            chain = Job.Info.Step.Chain()
            chain.procs = [['ExecuteInternal.create_preview_extract_audio_subtitles', path, asset_guid]]
            step.chains.append(chain)
            # Compose result
            result: Job.Emitted.Result = Job.Emitted.Result()
            result.handler = JobUtils.ResultHandlers.cpeas.__name__
            job.emitted.results.append(result)
            return job

        @staticmethod
        def _eascs(path, asset_guid, task_id):
            job: Job = Job('EAS: {}'.format(os.path.basename(path)), 0, task_id)
            job.type = Job.Type.EAS
            step: Job.Info.Step = Job.Info.Step()
            step.name = 'Create proxy, extract audio and subtitles'
            job.info.steps.append(step)
            chain = Job.Info.Step.Chain()
            chain.procs = [['ExecuteInternal.extract_audio_subtitles_create_slices', path, asset_guid]]
            step.chains.append(chain)
            # Compose result
            result: Job.Emitted.Result = Job.Emitted.Result()
            result.handler = JobUtils.ResultHandlers.cpeas.__name__
            job.emitted.results.append(result)
            return job

        @staticmethod
        def ingest_prepare(path):
            """
            Create a bunch of jobs (preview_extract_audio_subtitles), and results aggregator job
            :param path: path to source directory
            :return:
            """
            # Create task
            task: Task = Task()
            # Create final dummy job (trigger)
            agg: Job = Job('Ingest: aggregate assets', 0, task.guid)
            agg.type = Job.Type.INGEST_AGGREGATE | Job.Type.TRIGGER
            agg.dependsOnGroupId.new()
            group_id = agg.dependsOnGroupId

            # Filter inputs: get list of all files in directory
            inputs = []
            for root, firs, files in os.walk(path):
                inputs += [os.path.join(root, f) for f in files if len(f.split('.', 1)) == 2 and f.rsplit('.', 1)[1] in JobUtils.ACCEPTABLE_MEDIA_FILE_EXTENSIONS]
            if len(inputs) == 0:
                return

            # Create atomic jobs
            assets = []
            for inp in inputs:
                ass = str(uuid.uuid4())
                assets.append(ass)
                job = JobUtils.CreateJob._cpeas(inp, ass, task.guid)
                # TODO: add non-auto-commit connection to DBInterface, and register all jobs in single transaction
                job.status = Job.Status.INACTIVE
                # Add job to group
                job.groupIds.append(group_id)
                # Register job
                DBInterface.Job.register(job)

            res: Job.Emitted.Result = Job.Emitted.Result()
            res.handler = JobUtils.ResultHandlers.assets_to_ingest.__name__
            res.data = assets
            agg.emitted.results.append(res)
            # Register aggregator job
            DBInterface.Job.register(agg)

            # Change jobs statuses
            DBInterface.Job.set_fields_by_groups([str(group_id)], {'status': Job.Status.NEW})

        @staticmethod
        def ingest_prepare_sliced(path):
            """
            Ingest prepare step 0.1: get infos
            The pipeline is:
            ingest_prepare_sliced: info job => mediafiles_and_assets: create slices, audio/subs extract and and preview =>
                    _ips_p02_mediafiles_and_assets
            :param path: path to source directory
            :return:
            """
            if not os.path.isdir(path):
                Logger.error('Path {} is not a directory\n'.format(path))
                return 0
            paths = []
            names = []
            for root, firs, files in os.walk(path):
                for f in files:
                    ne = f.rsplit('.', 1)
                    if len(ne) == 2 and ne[1] in JobUtils.ACCEPTABLE_MEDIA_FILE_EXTENSIONS:
                        paths.append(os.path.join(root, f))
                        names.append(ne[0])
            if len(paths) == 0:
                Logger.error('Cannot find file(s) in {}\n'.format(path))
                return 0
            # Create task
            task: Task = Task()
            # Store common path to aliases as base
            base = os.path.commonpath((os.path.dirname(_) for _ in paths))
            # Create job
            job: Job = Job(name='MediaFiles and Assets for ingest', guid=0, task_id=task.guid)
            job.type = Job.Type.PROBE
            job.info.names = names
            job.info.aliases['base'] = base
            task.jobs.append(job.guid)
            step: Job.Info.Step = Job.Info.Step()
            step.name = 'MediaFiles and Assets for ingest'
            job.info.steps.append(step)
            # One chain for every input file
            for ci, p in enumerate(paths):
                srcn = 'src{:02d}'.format(ci)
                job.info.aliases[srcn] = p.replace(base, '${base}', 1)
                chain = Job.Info.Step.Chain()
                chain.procs = [
                    ['ExecuteInternal.create_mediafile_and_asset', '${{{}}}'.format(srcn), str(task.guid)]
                ]
                chain.result = 0
                step.chains.append(chain)
                result = Job.Emitted.Result()
                result.source.chain = ci
                job.emitted.results.append(result)
            job.emitted.handler = JobUtils.EmittedHandlers.mediafiles_and_assets.__name__

            DBInterface.Job.register(job)
            Logger.log('{}\n'.format(job.dumps(indent=2)))
            DBInterface.Task.register(task)
            return 1

        @staticmethod
        def _ips_p02_mediafiles_and_assets(params: List[dict]):
            """
            Ingest prepare step 0.2: create assets and jobs
            :param params: list of mediafiles, assets, transits and previews
            :return:
            """
            # param object from ffmpeg_utils.mediafile_asset_for_ingest
            # {
            #     'task': task_id,
            #     'asset': asset,
            #     'mediafile': mediafile,
            # }
            # Create group id to trigger final aggregative job
            group_id = Job.DependsOnGroupId(value=0)
            asset_ids = []
            task_id = None
            for param in params:
                task_id = param['task']
                asset: Asset = param['asset']
                mediafile: MediaFile = param['mediafile']
                asset_ids.append(str(asset.guid))

                adir = Storage.storage_path('archive', str(asset.guid))
                tdir = Storage.storage_path('transit', str(asset.guid))
                pdir = Storage.storage_path('preview', str(asset.guid))
                cdir = Storage.storage_path('cache', str(asset.guid))

                # archives: List[MediaFile] = []
                previews: List[MediaFile] = []
                transits: List[MediaFile] = []

                # Enumerate video tracks, create archive and preview mediafiles
                # For every video track create a job that marks out slices
                for ti, v in enumerate(mediafile.videoTracks):
                    vst = asset.videoStreams[ti]
                    vst.fpsOriginal.set(v.fps)
                    vst.fpsEncode.set2int(v.fps)
                    preview: MediaFile = v.ref_add()
                    # vt = copy.deepcopy(v)
                    archive_id = str(uuid.uuid4())
                    # archive: MediaFile = MediaFile(name='Archive: {}'.format(mediafile.name))
                    # archive_name = '{}.v{:02d}.archive.mp4'.format(archive.guid, ti)
                    # preview_name = '{}.v{:02d}.preview.mp4'.format(archive.guid, ti)
                    archive_name = '{}.v{:02d}.archive.mp4'.format(archive_id, ti)
                    preview_name = '{}.v{:02d}.preview.mp4'.format(mediafile.guid, ti)

                    # archive.master.guid = mediafile.guid.guid
                    # archive.source.path = os.path.join(adir.net_path, archive_name)
                    # archive.videoTracks.append(vt)
                    # archives.append(archive)
                    # v.extract = archive.guid
                    v.extract = archive_id
                    asset.mediaFilesExtra.append(Guid(value=archive_id))

                    preview.master.guid = mediafile.guid.guid
                    preview.name = 'Preview: {}'.format(mediafile.name)
                    preview.source.path = os.path.join(pdir.net_path, preview_name)
                    preview.source.url = '{}/{}'.format(pdir.web_path, preview_name)
                    previews.append(preview)

                    # A job to capture slices
                    job: Job = Job(name='split.v{}'.format(ti), guid=0, task_id=task_id)
                    job.type = Job.Type.SLICES_CREATE
                    job.groupIds.append(group_id)
                    job.info.paths = [
                        pdir.net_path,
                        adir.net_path,
                        cdir.net_path
                    ]
                    chain: Job.Info.Step.Chain = Job.Info.Step.Chain()
                    mf_dumps = mediafile.dumps()
                    chain.procs = [
                        ['ExecuteInternal.create_slices', mf_dumps, ti]
                    ]
                    step: Job.Info.Step = Job.Info.Step()
                    step.chains.append(chain)
                    job.info.steps.append(step)

                    # Result with captured slices
                    result: Job.Emitted.Result = Job.Emitted.Result()
                    job.emitted.results.append(result)

                    # Trigger (pass info to make post-job actions)
                    result: Job.Emitted.Result = Job.Emitted.Result()
                    result.source.step = -1
                    result.data = {
                        'task': task_id,
                        'src': mf_dumps,
                        'vti': ti,
                        'group_id': str(group_id),
                        # 'archive': archive.dumps(),
                        'archive_id': archive_id,
                        'archive_name': archive_name,
                        'preview': preview.dumps(),
                        'cropdetect': vst.cropdetect.dumps(),
                        'collector_id': str(vst.collector)
                    }
                    job.emitted.results.append(result)
                    job.emitted.handler = result.handler = JobUtils.EmittedHandlers.ips_p03_slices.__name__

                    # Register collector
                    DBInterface.Collector.register(
                        'Collector for videoStream #{} of asset {}'.format(ti, asset.guid),
                        str(vst.collector)
                    )

                    DBInterface.Job.register(job)

                filters = []
                outputs = []
                # subStreams: List[SubStream] = []
                # audioStreams: List[AudioStream] = []
                # Enumerate subtitles tracks, create previews and transit (extracted track) files
                for ti, s in enumerate(mediafile.subTracks):
                    # Special case for 1-track subtitles only
                    if len(mediafile.videoTracks) == 0 and len(mediafile.audioTracks) == 0 and len(
                            mediafile.subTracks) == 1:
                        subtitles = mediafile
                        st = s
                    else:
                        st = copy.deepcopy(s)
                        st.index = 0
                        subtitles: MediaFile = MediaFile(name='transit subtitles')
                        s.extract = subtitles.guid
                        subtitles.role = MediaFile.Role.TRANSIT
                        subtitles.master.set(mediafile.guid.guid)
                        subtitles.subTracks.append(st)
                        subtitles.source.path = os.path.join(tdir.net_path, '{}.s{:02d}.extract.mkv'.format(mediafile.guid, ti))
                        outputs.append('-map 0:s:{sti} -c:s copy {path}'.format(sti=ti, path=subtitles.source.path))
                        transits.append(subtitles)
                        asset.mediaFilesExtra.append(subtitles.guid)
                    preview_name = '{}.s{:02d}.preview.vtt'.format(subtitles.guid, ti)
                    subtitles_preview: MediaFile = MediaFile(name='preview-sub')
                    subtitles_preview.master.set(subtitles.guid.guid)
                    subtitles_preview.role = MediaFile.Role.PREVIEW
                    subtitles_preview.source.path = os.path.join(pdir.net_path, preview_name)
                    subtitles_preview.source.url = '{}/{}'.format(pdir.web_path, preview_name)
                    st.previews.append(str(subtitles_preview.guid))
                    outputs.append('-map 0:s:{sti} -c:s webvtt {path}'.format(sti=ti, path=subtitles_preview.source.path))
                    previews.append(subtitles_preview)

                    sub_stream: Asset.SubStream = Asset.SubStream()
                    sub_stream.program_in = 0
                    sub_stream.program_out = s.duration
                    sub_stream.layout = s.channel_layout
                    if s.tags and s.tags.language:
                        sub_stream.language = s.tags.language
                    chan = Stream.Channel()
                    chan.src_stream_index = ti
                    sub_stream.channels.append(chan)
                    asset.audioStreams.append(sub_stream)

                # Enumerate audio tracks, create previews and transit (extracted track) files
                for ti, a in enumerate(mediafile.audioTracks):
                    # Special case for 1-track audio only
                    if len(mediafile.videoTracks) == 0 and len(mediafile.subTracks) == 0 and len(
                            mediafile.audioTracks) == 1:
                        audio = mediafile
                        at = a
                    else:
                        at = copy.deepcopy(a)
                        audio: MediaFile = MediaFile(name='transit audio')
                        a.extract = audio.guid
                        audio.role = MediaFile.Role.TRANSIT
                        audio.master.set(mediafile.guid.guid)
                        audio.audioTracks.append(at)
                        audio.source.path = os.path.join(tdir.net_path, '{}.a{:02d}.extract.mkv'.format(mediafile.guid, ti))
                        outputs.append('-map 0:a:{ti} -c:a copy {path}'.format(ti=ti, path=audio.source.path))
                        transits.append(audio)
                        asset.mediaFilesExtra.append(audio.guid)
                    # Use silencedetect filter only for first track
                    # Using astats filter to measure audio levels because it's summary easier to capture than for ebur128
                    audio_filter = '[0:a:{ti}]astats,{sd}pan=mono|c0=c0[ap_{ti:02d}_00]'.format(ti=ti, sd='' if ti else 'silencedetect,')
                    for ci in range(a.channels):
                        preview_name = '{}.a{:02d}.c{:02d}.preview.mp4'.format(audio.guid, ti, ci)
                        audio_preview: MediaFile = MediaFile(name='preview-audio')
                        audio_preview.master.set(audio.guid.guid)
                        audio_preview.role = MediaFile.Role.PREVIEW
                        audio_preview.source.path = os.path.join(pdir.net_path, preview_name)
                        audio_preview.source.url = '{}/{}'.format(pdir.web_path, preview_name)
                        at.previews.append(str(audio_preview.guid))
                        if audio_filter is None:
                            audio_filter = '[0:a:{ti}]pan=mono|c0=c{ci}[ap_{ti:02d}_{ci:02d}]'.format(ti=ti, ci=ci)
                        filters.append(audio_filter)
                        audio_filter = None
                        outputs.append('-map [ap_{ti:02d}_{ci:02d}] -strict -2 -c:a aac -b:a 48k {path}'.format(ti=ti, ci=ci, path=audio_preview.source.path))
                        previews.append(audio_preview)

                    # Create AudioStream for asset
                    a_stream = Asset.AudioStream()
                    a_stream.program_in = 0
                    a_stream.program_out = a.duration
                    a_stream.layout = a.channel_layout
                    if ti == 0:
                        a_stream.collector.new()
                    if a.tags and a.tags.language:
                        a_stream.language = a.tags.language
                    for ci in range(a.channels):
                        chan = Stream.Channel()
                        chan.src_stream_index = ti
                        chan.src_channel_index = ci
                        a_stream.channels.append(chan)
                    asset.audioStreams.append(a_stream)

                # Create extract/preview job if needed
                if len(outputs):
                    # Finally, compose the command
                    command_cli = 'ffmpeg -y -i {src} -map_metadata -1 -filter_complex "{filters}" {outputs}'.format(
                        src=mediafile.source.path,
                        filters=';'.join(filters),
                        outputs=' '.join(outputs)
                    )
                    command_py = 'ffmpeg -y -i {src} -map_metadata -1 -filter_complex {filters} {outputs}'.format(
                        src=mediafile.source.path,
                        filters=';'.join(filters),
                        outputs=' '.join(outputs)
                    )
                    Logger.log('{}\n'.format(command_cli))

                    # Create job: single step, single chain, single proc
                    chain: Job.Info.Step.Chain = Job.Info.Step.Chain()
                    chain.procs = [command_py.split(' ')]
                    chain.return_codes = [[0]]
                    chain.progress.parser = 'ffmpeg_progress'
                    chain.progress.top = mediafile.format.duration
                    step: Job.Info.Step = Job.Info.Step()
                    step.chains.append(chain)
                    job: Job = Job('PEAS({})'.format(mediafile.name), 0, task_id)
                    job.type = Job.Type.PEAS
                    job.priority = Job.Priority.NORMAL
                    job.groupIds.append(group_id)
                    job.info.steps.append(step)
                    job.info.paths = [
                        pdir.net_path,
                        tdir.net_path
                    ]
                    # Create job: result to capture silence [and levels, ebur128, etc.] ***only for 1st audio track
                    result: Job.Emitted.Result = Job.Emitted.Result()
                    result.source.parser = 'ffmpeg_auto_text'
                    job.emitted.results.append(result)
                    # Create job: pass asset guid to result handler
                    result = Job.Emitted.Result()
                    result.source.step = -1
                    result.data = {
                        'asset': str(asset.guid)
                    }
                    job.emitted.results.append(result)
                    # Create job: the handler
                    job.emitted.handler = JobUtils.EmittedHandlers.ips_p03_audio_info.__name__

                    # Register asset and mediafile
                    DBInterface.Asset.set(asset)
                    DBInterface.MediaFile.set(mediafile)

                    # Register temporary mediafiles
                    for mf in previews + transits:
                        DBInterface.MediaFile.set(mf)

                    # Register job
                    DBInterface.Job.register(job)
                else:
                    Logger.error('JobUtils.CreateJob._ips_p02_mediafiles_and_assets: No outputs for {}\n'.format(param))

            if len(asset_ids):
                result = Job.Emitted.Result()
                result.source.step = -1
                result.data = {
                    'assets': asset_ids
                }
                # Create final aggregative job (trigger)
                agg: Job = Job('Ingest sliced: aggregate assets', 0, task_id)
                agg.type = Job.Type.INGEST_AGGREGATE | Job.Type.TRIGGER
                agg.emitted.results.append(result)
                agg.emitted.handler = JobUtils.EmittedHandlers.ips_p04_merge_assets.__name__
                agg.dependsOnGroupId.set(group_id)

                DBInterface.Job.register(agg)

        @staticmethod
        @tracer
        def _ips_p03_slices(slices, trig):
            #
            # Create compile job and set of encode jobs for single videoTrack
            # using captured slices
            # Logger.log('{}\n{}\n'.format(pformat(slices), pformat(trig)))
            # trig = {
            #     'task': task_id,
            #     'src': mf_dumps,
            #     'vti': ti,
            #     'group_id': str(group_id),
            #     # 'archive': archive.dumps(),
            #     'archive_id': archive_id,
            #     'archive_name': archive_name,
            #     'preview': preview.dumps(),
            #     'cropdetect': vst.cropdetect.dumps(),
            #     'collector_id': collector_id          # Collectors aggregate results from slices
            # }

            # def strslice(_s: MediaFile.VideoTrack.Slice):
            #     return 'pattern_offset={};length={};crc={}'.format(_s.pattern_offset, _s.length, ','.join([str(_) for _ in _s.crc]))
            task_id = trig['task']
            mf: MediaFile = MediaFile()
            # archive: MediaFile = MediaFile(guid=trig['archive_id'])
            preview: MediaFile = MediaFile()
            cropdetect: Asset.VideoStream.Cropdetect = Asset.VideoStream.Cropdetect()
            mf.update_str(trig['src'])
            vti = trig['vti']
            group_id = Guid(trig['group_id'])
            # archive.update_str(trig['archive'])

            preview.update_str(trig['preview'])
            cropdetect.update_str(trig['cropdetect'])

            cdir = Storage.storage_path('cache', str(mf.guid))
            # pdir = Storage.storage_path('preview', str(mf.guid))
            adir = Storage.storage_path('archive', str(mf.guid))

            archive_path = os.path.join(adir.net_path, trig['archive_name'])

            vt: MediaFile.VideoTrack = mf.videoTracks[vti]
            pvt: MediaFile.VideoTrack = preview.videoTracks[0]

            vt.slices = [MediaFile.VideoTrack.Slice(_) for _ in slices]
            DBInterface.MediaFile.update_videoTrack(mf, vti)

            # Get transform setup
            # fmap = JobUtils.PIX_FMT_MAP_X265['default'] if vt.pix_fmt not in JobUtils.PIX_FMT_MAP_X265 else JobUtils.PIX_FMT_MAP_X265[vt.pix_fmt]
            #
            # tmpl3 = '{x265} --input {{input}} --input-depth {d} --input-csp {csp}'.format(**fmap)
            # tmpl3 += ' --input-res {w}x{h} --fps {fps}'.format(w=vt.width, h=vt.height, fps=vt.fps.val())
            # if 'P' in fmap:
            #     tmpl3 += ' --profile {}'.format(fmap['P'])
            # tmpl3 += ' --allow-non-conformance --ref 3 --me umh --merange {}'.format(int(vt.width / 35))
            # tmpl3 += ' --no-open-gop --keyint 30 --min-keyint 5 --rc-lookahead 30 --bframes 3 --force-flush 1'
            # bitrate = JobUtils.calc_bitrate_x265_kbps(fmap, vt.width, vt.height, vt.fps.val())
            # tmpl3 += ' --bitrate {} --vbv-maxrate {} --vbv-bufsize {}'.format(bitrate, bitrate + (bitrate >> 1), bitrate + (bitrate >> 3))
            # tmpl3 += ' --output {output}'

            fmap = JobUtils.PIX_FMT_MAP_X264['default'] if vt.pix_fmt not in JobUtils.PIX_FMT_MAP_X264 else JobUtils.PIX_FMT_MAP_X264[vt.pix_fmt]

            # Archive file fps, width & height
            fps = Rational()
            fps.set2int(vt.fps)
            aw = vt.width
            ah = vt.height
            vflts = []
            if 't' in fmap:
                vflts.append('format={}'.format(fmap['t']))
            cdfs = cropdetect.filter_string()
            if cdfs:
                if cropdetect.w < vt.width or cropdetect.h < vt.height:
                    vflts.append(cdfs)
                    aw = cropdetect.w
                    ah = cropdetect.h

            tmpl3 = '{x264} --input-depth {d} --input-csp {csp}'.format(**fmap)
            tmpl3 += ' --input-res {w}x{h} --fps {fps}'.format(w=aw, h=ah, fps=fps)
            if 'P' in fmap:
                tmpl3 += ' --profile {}'.format(fmap['P'])
            tmpl3 += ' --ref 3 --me umh --merange {}'.format(int(vt.width / 35))
            tmpl3 += ' --keyint 30 --min-keyint 5 --rc-lookahead 30 --bframes 3'
            bitrate = JobUtils.calc_bitrate_x265_kbps(fmap, vt.width, vt.height, fps.val())
            tmpl3 += ' --bitrate {} --vbv-maxrate {} --vbv-bufsize {}'.format(bitrate, bitrate + (bitrate >> 1), bitrate + (bitrate >> 3))
            tmpl3 += ' --output {output} {input}'

            # 1 Create 2 concat jobs: for preview and for archive
            job_preview_concat: Job = Job(name='preview_concat', guid=0, task_id=task_id)
            job_preview_concat.type = Job.Type.SLICES_CONCAT
            job_preview_concat.groupIds.append(group_id)
            job_preview_concat.dependsOnGroupId.new()
            job_archive_concat: Job = Job(name='archive_concat', guid=0, task_id=task_id)
            job_archive_concat.type = Job.Type.SLICES_CONCAT
            job_archive_concat.groupIds.append(group_id)
            job_archive_concat.info.paths.append(adir.net_path)
            job_archive_concat.dependsOnGroupId = job_preview_concat.dependsOnGroupId
            # job_archive_concat.emitted.handler = JobUtils.ResultHandlers.ips_p03_slices_concat.__name__
            # Add result to archive concat job
            # result: Job.Emitted.Result = Job.Emitted.Result()
            # job_archive_concat.emitted.results.append(result)
            # # Second is a helper - it references results collector
            # result = Job.Emitted.Result()
            # result.data = {
            #     'collector_id': trig['collector_id']
            # }

            # 2 Create Nx2 encode jobs

            tmpl2 = 'ffmpeg -y -f rawvideo -s {w}:{h} -r {fps} -pix_fmt {pf} -nostats -i -'.format(w=vt.width, h=vt.height, fps=vt.fps, pf=vt.pix_fmt)
            if len(vflts):
                tmpl2 += ' -vf {}'.format(','.join(vflts))
            tmpl2 += ' -c:v rawvideo -f rawvideo -'
            tmpl2 += ' -vf format=yuv420p,scale={w}:{h},blackdetect=d=0.5:pic_th=0.99:pix_th=0.005,showinfo'.format(w=pvt.width, h=pvt.height)
            tmpl2 += ' -c:v libx264 -preset slow -g 30 -bf 3 -refs 2 -b:v 600k '

            overlap = 50
            segment_list_preview = ''
            segment_list_archive = ''
            jobs = []
            pslic: MediaFile.VideoTrack.Slice = None
            for idx, slic in enumerate(vt.slices + [None]):
                segment_path_preview = os.path.join(cdir.net_path, 'prv_{:03d}.h264'.format(idx))
                segment_path_archive = os.path.join(cdir.net_path, 'arch_{:03d}.hevc'.format(idx))
                segment_list_preview += 'file {}\n'.format(segment_path_preview)
                segment_list_archive += 'file {}\n'.format(segment_path_archive)
                job_preview_archive_slice: Job = Job(name='encode_slice_{:03d}'.format(idx), guid=0, task_id=task_id)
                job_preview_archive_slice.type = Job.Type.ENCODE_VIDEO
                job_preview_archive_slice.groupIds.append(job_preview_concat.dependsOnGroupId)

                # slice_start = 0.0
                # slice_frames = 0
                # slice_duration = 0.0

                if slic is None:
                    slice_start = pslic.time + pslic.pattern_offset / vt.fps.val()
                    slice_duration = vt.duration - slice_start
                    slice_frames = int(slice_duration *  vt.fps.val())
                    dur = vt.duration - pslic.time + 1
                    proc1 = '{trim} trim --pin {pin}'.format(trim=JobUtils.TRIMMER, pin=pslic.embed())
                elif pslic is None:
                    slice_start = 0.0
                    slice_duration = slic['time'] + slic['pattern_offset'] / vt.fps.val()
                    slice_frames = int(slice_duration * vt.fps.val())
                    dur = slic['time'] + (overlap + slic['pattern_offset']) / vt.fps.val()
                    proc1 = '{trim} trim --pout {pout}'.format(trim=JobUtils.TRIMMER, pout=slic.embed())
                else:
                    slice_start = pslic['time'] + pslic['pattern_offset'] / vt.fps.val()
                    slice_duration = slic['time'] + slic['pattern_offset'] / vt.fps.val() - slice_start
                    slice_frames = int(slice_duration * vt.fps.val())
                    dur = slic['time'] - pslic['time'] + (overlap + slic['pattern_offset'] - pslic['pattern_offset']) / vt.fps.val()
                    proc1 = '{trim} trim --pin {pin} --pout {pout}'.format(trim=JobUtils.TRIMMER, pin=pslic.embed(), pout=slic.embed())
                if pslic is None:
                    proc0 = 'ffmpeg -y -loglevel error -stats -i {i} -map v:{ti} -vsync 1 -r {fps} -t {t}'.format(i=mf.source.path, ti=vti, fps=vt.fps.dump_alt(), t=dur)
                else:
                    proc0 = 'ffmpeg -y -loglevel error -stats -ss {ss} -i {i} -map v:{ti} -vsync 1 -r {fps} -t {t}'.format(ss=pslic['time'], i=mf.source.path, ti=vti, fps=vt.fps.dump_alt(), t=dur)
                proc0 += ' -c:v rawvideo -f rawvideo -'
                proc1 += ' -s {} {} -p {}'.format(vt.width, vt.height, vt.pix_fmt)
                proc2 = tmpl2 + segment_path_preview
                proc3 = tmpl3.format(input='-', output=segment_path_archive)
                chain: Job.Info.Step.Chain = Job.Info.Step.Chain()
                chain.procs = [
                    proc0.split(' '),
                    proc1.split(' '),
                    proc2.split(' '),
                    proc3.split(' ')
                ]
                chain.return_codes = [
                    None,
                    None,
                    [0],
                    [0]
                ]
                chain.progress.capture = 0
                chain.progress.parser = 'ffmpeg_progress'
                chain.progress.top = dur

                step: Job.Info.Step = Job.Info.Step()
                step.chains.append(chain)

                job_preview_archive_slice.info.steps.append(step)

                # First result is a ffmpeg's stderr parsed
                result: Job.Emitted.Result = Job.Emitted.Result()
                result.source.proc = 2
                result.source.parser = 'ffmpeg_auto_text'
                job_preview_archive_slice.emitted.results.append(result)
                # Second is a helper - it supplies slice's start time and duration, points to results collector
                result = Job.Emitted.Result()
                result.source.step = -1
                result.data = {
                    'slice': {
                        'start': slice_start,
                        'frames': slice_frames,
                        'duration': slice_duration
                    },
                    'collector_id': trig['collector_id']
                }
                job_preview_archive_slice.emitted.results.append(result)
                # Single handler for 2 results
                job_preview_archive_slice.emitted.handler = JobUtils.EmittedHandlers.slice.__name__

                jobs.append(job_preview_archive_slice)

                pslic = slic

                # Logger.info('{} | {} | {} | {}\n\n'.format(proc0, proc1, proc2, proc3))

            # Write concat files
            concat_preview = os.path.join(cdir.net_path, 'preview.list')
            concat_archive = os.path.join(cdir.net_path, 'archive.list')
            os.makedirs(cdir.net_path, exist_ok=True)
            with open(concat_preview, 'w') as f:
                f.write(segment_list_preview)
            with open(concat_archive, 'w') as f:
                f.write(segment_list_archive)

            # Concat commands
            cprv = 'ffmpeg -y -safe 0 -loglevel error -stats -f concat -i {} -c copy {}'.format(concat_preview, preview.source.path)
            carc = 'ffmpeg -y -safe 0 -loglevel error -stats -f concat -i {} -c copy {}'.format(concat_archive, archive_path)

            ##################################################
            chain: Job.Info.Step.Chain = Job.Info.Step.Chain()
            chain.procs = [cprv.split(' ')]
            chain.return_codes = [[0]]
            chain.progress.capture = 0
            chain.progress.parser = 'ffmpeg_progress'

            step: Job.Info.Step = Job.Info.Step()
            step.chains.append(chain)
            job_preview_concat.info.steps.append(step)
            ##################################################
            chain: Job.Info.Step.Chain = Job.Info.Step.Chain()
            chain.procs = [carc.split(' ')]
            chain.return_codes = [[0]]
            chain.progress.capture = 0
            chain.progress.parser = 'ffmpeg_progress'

            step: Job.Info.Step = Job.Info.Step()
            step.chains.append(chain)
            job_archive_concat.info.steps.append(step)
            #==============
            chain: Job.Info.Step.Chain = Job.Info.Step.Chain()
            chain.procs = [
                [
                    'ExecuteInternal.combined_info',
                    '{{"guid": "{}"}}'.format(trig['archive_id']),
                    archive_path
                ]
            ]
            # Compose result that update archive media file
            result = Job.Emitted.Result()
            result.handler = JobUtils.ResultHandlers.mediafile.__name__
            result.source.step = len(job_archive_concat.info.steps)
            job_archive_concat.emitted.results.append(result)

            step: Job.Info.Step = Job.Info.Step()
            step.chains.append(chain)
            job_archive_concat.info.steps.append(step)

            Logger.info('Concat preview command: {}\nConcat archive command: {}\n'.format(cprv, carc))

            # Register jobs
            for job in jobs:
                DBInterface.Job.register(job)

            DBInterface.Job.register(job_preview_concat)
            DBInterface.Job.register(job_archive_concat)

        @staticmethod
        def mediafile_by_asset(asset: Asset):
            pass

        # @staticmethod
        # def asset_to_mediafile(asset: Asset):
        #     # Sample code that creates a set of jobs to compile single mediafile using asset data
        #     media_files = []
        #
        #     for idx, guid in enumerate(asset.mediaFiles):
        #         mf: MediaFile = DBInterface.MediaFile.get(guid)
        #         media_files.append(mf)
        #     asset.mediaFiles = media_files
        #     if type(asset.mediaFilesExtra) is list:
        #         media_files_extra = []
        #         for idx, guid in enumerate(asset.mediaFilesExtra):
        #             mf: MediaFile = DBInterface.MediaFile.get(guid)
        #             media_files_extra.append(mf)
        #         asset.mediaFilesExtra = media_files_extra
        #
        #     job: Job = Job(name='asset to mediafile', guid=0)
        #     job.type = Job.Type.ENCODE_VIDEO | Job.Type.ENCODE_AUDIO
        #     step: Job.Info.Step = Job.Info.Step()
        #     step.name = 'Create media file using asset'
        #     job.info.steps.append(step)
        #     chain = Job.Info.Step.Chain()
        #     Logger.log('{}\n'.format(asset))
        #     chain.procs = [['ExecuteInternal.asset_to_mediafile', Exchange.object_encode(asset)]]
        #     step.chains.append(chain)
        #     # Compose result
        #     job.emitted.results.append(Job.Emitted.Result())
        #     job.emitted.handler = JobUtils.EmittedHandlers.asset_to_mediafile.__name__
        #
        #     DBInterface.Job.register(job)

    class ResultHandlers:

        class default:
            # Default handler for 'emitted' object
            @staticmethod
            def handler(emit: Job.Emitted, idx: int):
                # r = emit.results[idx]
                pass

        class mediafile:
            @staticmethod
            def handler(emit: Job.Emitted, idx: int):
                Logger.info('{}\n'.format(emit.dumps()))
                r = emit.results[idx]
                mf: MediaFile = r.data
                Logger.error('{}\n{}\n'.format(mf.dumps(indent=2), mf.__dict__.keys()))
                # exit(1)
                DBInterface.MediaFile.set(mf)

        class ips_p02_mediafiles:
            @staticmethod
            def handler(emit: Job.Emitted, idx: int):
                # r = emit.results[idx]
                mfs = [_.data for _ in emit.results[:idx]]
                JobUtils.CreateJob._ips_p02_mediafiles(mfs)

        class ips_p03_slices_concat:
            @staticmethod
            @tracer
            def handler(emit: Job.Emitted, idx: int):
                pass

        class ips_p03_assets:
            @staticmethod
            def handler(emit: Job.Emitted, idx: int):
                r = emit.results[idx]
                # res is a list
                #     'mediafile': mf,
                #     'slices': []  # Slice data

                # job_final: Job = Job()
                # job_final.dependsOnGroupId.new()

                # def strslice(_s):
                #     return 'pattern_offset={};length={};crc={}'.format(_s['pattern_offset'], _s['length'], ','.join([str(_) for _ in _s['crc']]))
                #
                # jobs = []
                # results = r.data
                # overlap = 50
                # # Enumerate files
                # for fi, res in enumerate(results):
                #         # Mediafile is not registered yet
                #         mf: MediaFile = res['mediafile']
                #         mf.guid.new()
                #         cdir = Storage.storage_path('cache', str(mf.guid))
                #         pdir = Storage.storage_path('preview', str(mf.guid))
                #         if 'slices' in res and len(res['slices']) > 0:
                #             # Enumerate sliced videoTracks creating concat job for every vt
                #             for vti, slices in enumerate(res['slices']):
                #                 vt: MediaFile.VideoTrack = mf.videoTracks[vti]
                #                 # Get transform setup
                #                 fmap = JobUtils.PIX_FMT_MAP['default'] if vt.pix_fmt not in JobUtils.PIX_FMT_MAP else JobUtils.PIX_FMT_MAP[vt.pix_fmt]
                #                 tmpl3 = '{c} --input - --input-depth {d} --input-csp {csp}'.format(**fmap)
                #                 tmpl3 += ' --input-res {w}x{h} --fps {fps}'.format(w=vt.width, h=vt.height, fps=vt.fps.val())
                #                 if 'P' in fmap:
                #                     tmpl3 += ' --profile {}'.format(fmap['P'])
                #                 tmpl3 += ' --allow-non-conformance --ref 3 --me umh --merange {}'.format(int(vt.width/35))
                #                 tmpl3 += ' --no-open-gop --keyint 30 --min-keyint 5 --rc-lookahead 30 -bframes 3 --force-flush 1'
                #                 bitrate = JobUtils.calc_bitrate_x265_kbps(fmap, vt.width, vt.height, vt.fps.val())
                #                 tmpl3 += ' --bitrate {} --vbv-maxrate {} --vbv-bufsize {}'.format(bitrate, bitrate + (bitrate >> 1), bitrate + (bitrate >> 3))
                #                 tmpl3 += ' --output '
                #
                #                 # Create video track preview
                #                 preview = vt.ref_add()
                #                 preview.name = 'preview-video#{}'.format(vti)
                #                 preview.source.path = os.path.join(pdir.net_path, '{}.v{}.preview.mp4'.format(mf.guid, vti))
                #                 preview.source.url = '{}/{}.v{}.preview.mp4'.format(pdir.web_path, mf.guid, vti)
                #                 pvt: MediaFile.VideoTrack = preview.videoTracks[0]
                #                 #1 Create 2 concat jobs: for preview and for archive
                #                 job_preview_concat: Job = Job(guid=0)
                #                 job_preview_concat.groupIds.append(job_final.dependsOnGroupId)
                #                 job_preview_concat.dependsOnGroupId.new()
                #                 job_archive_concat: Job = Job(guid=0)
                #                 job_archive_concat.groupIds.append(job_final.dependsOnGroupId)
                #                 job_archive_concat.dependsOnGroupId = job_preview_concat.dependsOnGroupId
                #                 #2 Create Nx2 encode jobs
                #
                #                 tmpl2 = 'ffmpeg -y -s {w}:{h} -r {fps} -pix_fmt {pf} -nostats -i -'.format(w=vt.width, h=vt.height, fps=vt.fps.val(), pf=vt.pix_fmt)
                #                 tmpl2 += ' -c:v rawvideo -f rawvideo -'
                #                 tmpl2 += ' -vf format=yuv420p,scale={w}:{h},blackdetect=d=0.5:pic_th=0.99:pix_th=0.005,showinfo'.format(w=pvt.width, h=pvt.height)
                #                 tmpl2 += ' -c:v libx264 -preset slow -g 30 -bframes 3 -refs 2 -b:v 600k '
                #
                #
                #                 segment_list_x264 = ''
                #                 segment_list_x265 = ''
                #                 pslic = None
                #                 for slic in res['slices'] + [None]:
                #                     segment_path_x264 = os.path.join(cdir.net_path, 'prv_{:03d}.h264')
                #                     segment_path_x265 = os.path.join(cdir.net_path, 'arch_{:03d}.hevc')
                #                     segment_list_x264 += 'file {}\n'.format(segment_path_x264)
                #                     segment_list_x265 += 'file {}\n'.format(segment_path_x265)
                #                     job_preview_archive_slice: Job = Job(guid=0)
                #                     job_preview_archive_slice.groupIds.append(job_preview_concat.dependsOnGroupId)
                #
                #                     if slic is None:
                #                         dur = vt.duration - pslic['time'] + 1
                #                         proc1 = '{trim} trim --pin {pin}'.format(trim=JobUtils.TRIMMER, pin=strslice(pslic))
                #                     elif pslic is None:
                #                         dur = slic['time'] + (overlap + slic['pattern_offset']) / vt.fps.val()
                #                         proc1 = '{trim} trim --pout {pout}'.format(trim=JobUtils.TRIMMER, pout=strslice(slic))
                #                     else:
                #                         dur = slic['time'] - pslic['time'] + (overlap + slic['pattern_offset'] - pslic['pattern_offset']) / vt.fps.val()
                #                         proc1 = '{trim} trim --pin {pin} --pout {pout}'.format(trim=JobUtils.TRIMMER, pin=strslice(pslic), pout=strslice(slic))
                #                     if pslic is None:
                #                         proc0 = 'ffmpeg -y -loglevel error -stats -i {i} -map v:{ti} -vsync 1 -r {fps} -t {t}'.format(i=mf.source.path, ti=vti, fps=vt.fps.dump_alt(), t=dur)
                #                     else:
                #                         proc0 = 'ffmpeg -y -loglevel error -stats -ss {ss} -i {i} -map v:{ti} -vsync 1 -r {fps} -t {t}'.format(ss=pslic['time'], i=mf.source.path, ti=vti, fps=vt.fps.dump_alt(), t=dur)
                #                     proc0 += ' -c:v rawvideo -f rawvideo -'
                #
                #                     proc1 += ' -s {} {} -p {}'.format(vt.width, vt.height, vt.pix_fmt)
                #
                #                     proc2 = tmpl2 + segment_path_x264
                #
                #                     proc3 = tmpl3 + segment_path_x265
                #
                #                     chain: Job.Info.Step.Chain = Job.Info.Step.Chain()
                #                     chain.procs = [
                #                         proc0.split(' '),
                #                         proc1.split(' '),
                #                         proc2.split(' '),
                #                         proc3.split(' ')
                #                     ]
                #                     chain.progress.capture = 0
                #                     chain.progress.parser = 'ffmpeg_progress'
                #                     step: Job.Info.Step = Job.Info.Step()
                #                     step.chains.append(chain)
                #
                #                     job_preview_archive_slice.info.steps.append(step)
                #
                #                     result: Job.Emitted.Result = Job.Emitted.Result()
                #                     result.handler = JobUtils.ResultHandlers.pa_slice.__name__
                #                     result.source.proc = 2
                #                     result.source.parser = 'ffmpeg_auto_text'
                #
                #                     job_preview_archive_slice.emitted.results.append(result)
                        # else:
                            # Create one EAS job

        class cpeas:
            @staticmethod
            def handler(emit: Job.Emitted, idx: int):
                r = emit.results[idx]
                # Parse results derived from 'internal_create_preview_extract_audio_subtitles'
                # Logger.critical(r.data)
                res = r.data
                DBInterface.Asset.set(res['asset'])
                for mf in res['trans'] + res['previews'] + res['archives']:
                    DBInterface.MediaFile.set(mf)
                DBInterface.MediaFile.set(res['src'])

        class assets_to_ingest:
            @staticmethod
            def handler(emit: Job.Emitted, idx: int):
                r = emit.results[idx]

                guid = merge_assets_create_interaction(r.data)
                Logger.log('assets_to_ingest: interaction created {}\n'.format(guid))
                # if len(r.data) == 1:
                #     asset_guid = r.data[0]
                # elif len(r.data) > 1:
                #     assts = DBInterface.Asset.records(r.data)
                #     assm = {}
                #     for i, asst in enumerate(assts):
                #         assm[str(asst['guid'])] = i
                #     assets = [assts[assm[aid]] for aid in r.data]
                #     asset = merge_assets(assets)
                #     asset.name = 'merged'
                #     DBInterface.Asset.set(asset)
                #     asset_guid = str(asset.guid)
                # # Create Interaction
                # inter = Interaction()
                # inter.guid.new()
                # inter.name = 'inter'
                # inter.assetIn.set(asset_guid)
                # inter.assetOut = None
                # DBInterface.Interaction.set(inter)

    class EmittedHandlers:
        # Handlers for Job.Emitted (results list) objects
        class default:
            # Default handler for 'emitted' object
            @staticmethod
            def handler(emit: Job.Emitted):
                pass

        class mediafiles_and_assets:
            @staticmethod
            def handler(emit: Job.Emitted):
                # Logger.warning('{}\n'.format(emit.dumps(indent=2)))
                params = [_.data for _ in emit.results]
                JobUtils.CreateJob._ips_p02_mediafiles_and_assets(params)

        # class asset_to_mediafile:
        #     @staticmethod
        #     def handler(emit: Job.Emitted):
        #         mf: MediaFile = Exchange.object_decode(emit.results[0].data)
        #         Logger.error('{}\n'.format(mf.dumps(indent=2)))
        #         exit(1)

        class ips_p03_slices:
            @staticmethod
            def handler(emit: Job.Emitted):
                slices = emit.results[0].data
                trig = emit.results[1].data
                JobUtils.CreateJob._ips_p03_slices(slices, trig)

        class ips_p03_audio_info:
            # TODO: we should bind captured silencedetect info to master asset/file
            @staticmethod
            def handler(emit: Job.Emitted):
                # emit.results[0] = audio scan info: silencedetect, levels, etc
                # emit.results[1] = {'asset': asset_id}

                sd = emit.results[0]['data']['silencedetect'] if 'silencedetect' in emit.results[0]['data'] else []
                astats = astats_to_model(emit.results[0]['data']['astats']) if 'astats' in emit.results[0]['data'] else []

                asset_id = emit.results[-1]['data']['asset']
                asset: Asset = DBInterface.Asset.get(asset_id)
                if asset.audioStreams and len(asset.audioStreams):
                    if len(asset.audioStreams) != len(astats):
                        Logger.error('astats and audioStreams count differs!\n')
                    for i, astr in enumerate(asset.audioStreams):
                        cguid = astr['collector']
                        collector: Collector = Collector(name='Audio info #{}'.format(i), guid=cguid)
                        if i == 0:
                            collector.audioResults.silencedetect = [json.dumps(_) for _ in sd]
                        collector.audioResults.astats = astats[i]
                        DBInterface.Collector.set(collector)
                # exit(1)

        class ips_p04_merge_assets:
            @staticmethod
            def handler(emit: Job.Emitted):
                asset_ids = emit.results[0].data['assets']
                # Read assets
                assets = DBInterface.Asset.records(asset_ids)
                for ass in assets:
                    asset: Asset = Asset()
                    asset.update_json(ass)
                    Logger.error('\n{}\n'.format(asset.dumps(indent=2)))
                    if type(asset.videoStreams) is list and len(asset.videoStreams) > 0:
                        vstr: Asset.VideoStream = asset.videoStreams[0]
                        # This collector contains blackdetect data captured from slices
                        collector_v: Collector = DBInterface.Collector.get(vstr.collector)
                        # Merge sliced blacks
                        blacks = []
                        silences = []
                        for ctd in collector_v.sliceResults:
                            # rec = json.loads(ctd)
                            # if 'blackdetect' in rec:
                            if ctd.blackdetect:
                                for bd in ctd.blackdetect:
                                    blacks.append([[ctd.start + float(bd['black_start']), -1], [ctd.start + float(bd['black_end']), 1]])
                        blacks.sort()
                        # Merge overlapped blackdetects
                        blacks_filtered = []
                        j = 0
                        for i in range(len(blacks)):
                            if i == 0:
                                blacks_filtered += blacks[i]
                                j += 2
                            else:
                                if blacks[i][0][0] - blacks[i-1][1][0] > 0.1:
                                    blacks_filtered += blacks[i]
                                    j += 2
                                else:
                                    blacks_filtered[j][0] = blacks[i][1][0]
                        if type(asset.audioStreams) is list and len(asset.audioStreams) > 0:
                            astr = asset.audioStreams[0]
                            collector_a: Collector = DBInterface.Collector.get(astr.collector)
                            Logger.error('\n{}\n'.format(collector_a.dumps(indent=2)))
                            for ctd in collector_a.audioResults.silencedetect:
                                rec = json.loads(ctd)
                                if 'silence_start' in rec:
                                    silences.append([float(rec['silence_start']), -1])
                                elif 'silence_end' in rec:
                                    if len(silences) == 0:
                                        silences.append([astr.program_in, -1])
                                    silences.append([float(rec['silence_end']), 1])
                                    # else:
                                    #     Logger.warning('silencedetect: silence_end without silence_start\n')
                            if len(silences) > 0 and len(silences[-1]) == 1:
                                silences[-1].append(astr.program_out)

                        Logger.critical('\n{}\n\n{}\n\n'.format(blacks_filtered, silences))

                        program_in = vstr.program_in
                        program_out = vstr.program_out
                        if len(blacks_filtered):
                            bound_in = min(program_out / 2.0, 200.0)
                            bound_out = program_out / 2.0
                            s = 2 if len(silences) else 1
                            silent_dark = False
                            for bs in sorted(blacks_filtered + silences):
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
                            vstr.program_in = program_in
                            vstr.program_out = program_out
                            asset.videoStreams[0] = vstr #json.loads(vstr.dumps())
                            # vstrs = json.dumps(asset.videoStreams)
                            DBInterface.Asset.update_videoStreams(asset)

                guid = merge_assets_create_interaction(asset_ids)
                Logger.log('assets_to_ingest: interaction created {}\n'.format(guid))
                return
                # if len(asset_ids) == 1:
                #     asset_guid = asset_ids[0]
                # elif len(asset_ids) > 1:
                #     # assets = DBInterface.Asset.records(r.data)
                #     assm = {}
                #     for i, asst in enumerate(assets):
                #         assm[str(asst['guid'])] = i
                #     assets = [assts[assm[aid]] for aid in r.data]
                #     asset = merge_assets(assets)
                #     asset.name = 'merged'
                #     DBInterface.Asset.set(asset)
                #     asset_guid = str(asset.guid)
                # # Create Interaction
                # inter = Interaction()
                # inter.guid.new()
                # inter.name = 'inter'
                # inter.assetIn.set(asset_guid)
                # inter.assetOut = None
                # DBInterface.Interaction.set(inter)
                #
                # exit(1)

                coll_a_collected = [
                  {
                    "silence_start": "0.0426667"
                  },
                  {
                    "silence_end": "30.0747",
                    "silence_duration": "30.032"
                  },
                  {
                    "silence_start": "40.064"
                  },
                  {
                    "silence_end": "50.2987",
                    "silence_duration": "10.2347"
                  },
                  {
                    "silence_start": "73.1307"
                  },
                  {
                    "silence_end": "86.5013",
                    "silence_duration": "13.3707"
                  },
                  {
                    "silence_start": "670.016"
                  }
                ]

                coll_v = {
                  "guid": "8d53af8b-a647-4f8b-a470-cbbc36501f90",
                  "name": "Collector for videoStream #0 of asset ba2282c4-6331-4502-aaa9-9",
                  "ctime": "2017-10-15 14:27:31.796714",
                  "mtime": "2017-10-15 14:27:31.796714",
                  "collected": [
                    "{\"start\": 0.0, \"frames\": 5706, \"duration\": 228.24333333333334, \"blackdetect\": [{\"black_start\": \"0\", \"black_end\": \"30.08\", \"black_duration\": \"30.08\"}, {\"black_start\": \"40.08\", \"black_end\": \"50.08\", \"black_duration\": \"10\"}]}",
                    "{\"start\": 228.24333333333334, \"frames\": 1193, \"duration\": 47.72333333333336}",
                    "{\"start\": 275.9666666666667, \"frames\": 1213, \"duration\": 48.52333333333331}",
                    "{\"start\": 324.49, \"frames\": 2382, \"duration\": 95.28666666666669}",
                    "{\"start\": 419.7766666666667, \"frames\": 1204, \"duration\": 48.1633333333333}",
                    "{\"start\": 467.94, \"frames\": 3588, \"duration\": 143.53000000000003}",
                    "{\"start\": 611.47, \"frames\": 2396, \"duration\": 95.84666666666669, \"blackdetect\": [{\"black_start\": \"63.68\", \"black_end\": \"93.68\", \"black_duration\": \"30\"}]}",
                    "{\"start\": 707.3166666666667, \"frames\": 1194, \"duration\": 47.76333333333332, \"blackdetect\": [{\"black_start\": \"13.16\", \"black_end\": \"23.16\", \"black_duration\": \"10\"}, {\"black_start\": \"38.16\", \"black_end\": \"48\", \"black_duration\": \"9.84\"}]}"
                  ]
                }

                r = {
                    "guid": "a842c1c0-64f9-4b57-ab11-1f9e46da7067",
                    "name": "Asset for ",
                    "ctime": "2017-10-15 14:27:31.782852",
                    "mtime": "2017-10-15 14:27:31.782852",
                    "mediaFiles": [
                    "74d333ce-9d0f-40c8-8f51-4bcc98c96271"
                    ],
                    "audioStreams": [
                    {
                      "layout": "5.1(side)",
                      "channels": [
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 0
                        },
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 1
                        },
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 2
                        },
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 3
                        },
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 4
                        },
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 5
                        }
                      ],
                      "language": "rus",
                      "program_in": 0,
                      "program_out": 755.104,
                      "collector": "45a77bcd-b721-409c-ada8-fd6b6b01f839"
                    }
                    ]
                }
                r = {
                    "guid": "b6800315-9b3d-4db3-b44e-e3314550eb03",
                    "name": "Asset for ",
                    "ctime": "2017-10-15 14:27:31.791830",
                    "mtime": "2017-10-15 14:27:31.791830",
                    "mediaFiles": [
                    "bce4a6aa-5f69-40b1-849e-a3b96559b013"
                    ],
                    "audioStreams": [
                    {
                      "layout": "5.1(side)",
                      "channels": [
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 0
                        },
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 1
                        },
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 2
                        },
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 3
                        },
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 4
                        },
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 5
                        }
                      ],
                      "language": "eng",
                      "program_in": 0,
                      "program_out": 755.104,
                      "collector": "0c4319fe-230b-4624-92c6-5ae36fe6047f"
                    }
                    ]
                }

                r = {
                    "guid": "ba2282c4-6331-4502-aaa9-97824e9f21ca",
                    "name": "Asset for ",
                    "ctime": "2017-10-15 14:27:31.807259",
                    "mtime": "2017-10-15 14:27:31.807259",
                    "mediaFiles": [
                    "2d984fdc-1d80-40af-912a-a0e21e90d4b7"
                    ],
                    "videoStreams": [
                    {
                      "channels": [
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 0
                        }
                      ],
                      "program_in": 0.0,
                      "program_out": 755.12,
                      "collector": "8d53af8b-a647-4f8b-a470-cbbc36501f90",
                      "cropdetect": {
                        "w": 960,
                        "h": 400,
                        "x": 32,
                        "y": 184,
                        "sar": 1.0,
                        "aspect": 2.4
                      }
                    }
                    ],
                    "audioStreams": [
                    {
                      "layout": "stereo",
                      "channels": [
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 0
                        },
                        {
                          "src_stream_index": 0,
                          "src_channel_index": 1
                        }
                      ],
                      "language": "rus",
                      "program_in": 0,
                      "program_out": 755.12,
                      "collector": "642ecb59-e301-4df0-9379-89fb72a56f2b"
                    }
                    ]
                }

        class slice:
            @staticmethod
            def handler(emit: Job.Emitted):
                # r0.data is an output of parser 'ffmpeg_auto_text'
                # r0.data = {
                #     'showinfo': [...],
                #     'blackdetect': [...]      # may not present if no blackdetect
                # }
                # r1.data = {
                #     'slice': {
                #         'start': slice_start,
                #         'frames': slice_frames,
                #         'duration': slice_duration
                #     },
                #     'collector_id': trig['collector_id']
                # }
                r0: Job.Emitted.Result = emit.results[0]
                # showinfo is filter with index
                if 'showinfo' in r0.data:
                    r0.data.pop('showinfo')
                r1: Job.Emitted.Result = emit.results[1]
                Logger.info('{}\n'.format(r0))
                Logger.info('{}\n'.format(r1))
                sr: Collector.SliceResult = Collector.SliceResult()
                sr.update_json(r0.data)
                sr.update_json(r1.data['slice'])
                Logger.warning('{}\n'.format(sr))
                DBInterface.Collector.append_slice_result(r1.data['collector_id'], sr)

    @staticmethod
    def process_results(job: Job):
        for i, r in enumerate(job.emitted.results):
            hr = JobUtils.ResultHandlers.default
            try:
                hr = JobUtils.ResultHandlers.__dict__[r.handler]
            except:
                pass
            hr.handler(job.emitted, i)
        he = JobUtils.EmittedHandlers.default
        try:
            he = JobUtils.EmittedHandlers.__dict__[job.emitted.handler]
        except:
            pass
        he.handler(job.emitted)

    @staticmethod
    def get_assets_by_uids(uids):
        return DBInterface.Asset.records(uids)

    @staticmethod
    def _resolve_aliases(params):
        collection = params['collection']
        text: str = params['text']
        resolved = 0
        missed = 0
        while True:
            aliases = set(re.findall(r'\${([a-zA-Z0-9\-_]+?)}', text))
            if len(aliases) == missed:
                break
            missed = 0
            for v in aliases:
                if v in collection:
                    text = text.replace('${{{0}}}'.format(v), collection[v])
                    resolved += 1
                else:
                    missed += 1
                    Logger.warning('resolve_aliases: {0} value not found\n'.format(v))
                    # post-replace loop to resolve inherited links
        # params['resolved'] = resolved
        if resolved > 0:
            params['json'] = json.loads(text)
        return resolved

    @staticmethod
    def resolve_aliases(job: Job):
        aliases = job.info.aliases
        # Aliases must contain 'tmp' and 'guid'
        aliases['guid'] = str(job.guid)

        params = {
            'collection': aliases,
            'text': job.info.dumps()
        }
        if JobUtils._resolve_aliases(params):
            # Clear all lists in info
            job.info.reset_lists()
            job.info.update_json(params['json'])

    # if 'JobUtils' not in globals() or 'RESULTS' not in globals()['JobUtils'].__dict__:
    #     RESULTS = Results()
