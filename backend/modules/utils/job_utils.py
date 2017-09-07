# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import re
import os
import json
import uuid
import pickle
import base64
from pprint import pformat
from typing import List
from modules.models.job import Job
from modules.models.asset import Asset, VideoStream, AudioStream, SubStream, Stream
from modules.models.mediafile import MediaFile
from modules.models.interaction import Interaction
from modules.utils.database import DBInterface
from .log_console import Logger, tracer
from .storage import Storage
from .parsers import Parsers


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

    asset: Asset = Asset()
    vii = 0
    aii = 0
    sii = 0
    Logger.log('merge_assets:\n\n')
    for a in assets:
        Logger.warning('{}\n\n'.format(pformat(a)))

        vss = _advance_streams(VideoStream, a['videoStreams'], vii)
        vii += len(vss)
        ass = _advance_streams(AudioStream, a['audioStreams'], aii)
        aii += len(ass)
        sss = _advance_streams(SubStream, a['subStreams'], sii)
        sii += len(sss)

        Logger.warning('vss: {}\nass: {}\n sss: {}\n\n'.format(vss, ass, sss))

        asset.videoStreams += vss
        asset.audioStreams += ass
        asset.subStreams += sss

        asset.mediaFiles += [Asset.MediaFile(_) for _ in a['mediaFiles']]

    return asset


class JobUtils:
    TRIMMER = '/home/tim/projects/trim/bin/x64/Debug/trim.out'

    ACCEPTABLE_MEDIA_FILE_EXTENSIONS = {
        'm2ts', 'm2v', 'mov', 'mkv', 'mp4', 'mpeg', 'mpg', 'mpv',
        'mts', 'mxf', 'webm', 'ogg', 'gp3', 'avi', 'vob', 'ts',
        '264', 'h264',
        'flv', 'f4v', 'wav', 'ac3', 'aac', 'mp2', 'mp3', 'mpa',
        'sox', 'dts', 'dtshd'
    }

    PIX_FMT_MAP = {
        'yuv420p':     {                    'd': 8, 'csp': 'i420', 'P': 'main',        'c': 'x264.08', 'bs': 0.15},     # Bitrate scale = depth * csp / 640
        'yuv422p':     {                    'd': 8, 'csp': 'i422',                     'c': 'x264.08', 'bs': 0.2},      # No standard profile for 8-bit 422
        'yuv420p10le': {                    'd': 10, 'csp': 'i420', 'P': 'main10',     'c': 'x264.10', 'bs': 0.1875},
        'yuv422p10le': {                    'd': 10, 'csp': 'i422', 'P': 'main422-10', 'c': 'x264.10', 'bs': 0.25},
        'yuv420p10be': {'t': 'yuv420p10le', 'd': 10, 'csp': 'i420', 'P': 'main10',     'c': 'x264.10', 'bs': 0.1875},
        'yuv422p10be': {'t': 'yuv422p10le', 'd': 10, 'csp': 'i422', 'P': 'main422-10', 'c': 'x264.10', 'bs': 0.25},
        'yuv420p12le': {                    'd': 12, 'csp': 'i420', 'P': 'main12',     'c': 'x264.12', 'bs': 0.225},
        'yuv422p12le': {                    'd': 12, 'csp': 'i422', 'P': 'main422-12', 'c': 'x264.12', 'bs': 0.3},
        'yuv420p12be': {'t': 'yuv420p12le', 'd': 12, 'csp': 'i420', 'P': 'main12',     'c': 'x264.12', 'bs': 0.225},
        'yuv422p12be': {'t': 'yuv422p12le', 'd': 12, 'csp': 'i422', 'P': 'main422-12', 'c': 'x264.12', 'bs': 0.3},
        'default':     {'t': 'yuv422p12le', 'd': 12, 'csp': 'i422', 'P': 'main422-12', 'c': 'x264.12', 'bs': 0.3}
    }

    @staticmethod
    def calc_bitrate_x265_kbps(fmap, w, h, fps):
        br = 400 + int(0.001 * w * h * fps * fmap['bs'])
        br -= br % 10
        return br

    class CreateJob:
        @staticmethod
        def media_info(path, names: List[str]):
            """
            Create a job that analyzes source(s) and creates MediaFile(s)
            :param path: path to file or directory
            :param names: strings that may help to identify media
            :return: job GUID or None
            """
            paths = []
            if os.path.isfile(path):
                paths.append(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for f in files:
                        paths.append(os.path.join(root, f))
                if len(paths) == 0:
                    Logger.error('Cannot find file(s) in {}\n'.format(path))
                    return None
            # Store common path to aliases as base
            base = os.path.commonpath((os.path.dirname(_) for _ in paths))
            # Create job
            job: Job = Job()
            job.type = Job.Type.PROBE
            job.info.names = names
            job.info.aliases['base'] = base
            step: Job.Info.Step = Job.Info.Step()
            step.name = 'Get combined info'
            job.info.steps.append(step)
            for i, p in enumerate(paths):
                uidn = 'uid{:02d}'.format(i)
                srcn = 'src{:02d}'.format(i)
                # Set ailases
                job.info.aliases[srcn] = p.replace(base, '${base}', 1)
                job.info.aliases[uidn] = str(uuid.uuid4())
                # Compose chain
                chain = Job.Info.Step.Chain()
                chain.procs = [
                    ['internal_combined_info', '{"guid":"${{{}}}"}'.format(uidn), '${{{}}}'.format(srcn)]
                ]
                chain.result = 0
                step.chains.append(chain)
                # Compose result
                result = Job.Result()
                result.handler = JobUtils.Results.mediafile.__name__
                # result.predefined = {"guid": '${{{}}}'.format(uidn), "source": {"url": '${{{}}}'.format(srcn)}}
                job.results.append(result)
            # Register job
            DBInterface.Job.register(job)
            return job

        @staticmethod
        def _cpeas(path, asset_guid):
            job: Job = Job()
            job.guid.new()
            job.name = 'CPEAS: {}'.format(os.path.basename(path))
            job.type = Job.Type.CPEAS
            step: Job.Info.Step = Job.Info.Step()
            step.name = 'Create proxy, extract audio and subtitles'
            job.info.steps.append(step)
            chain = Job.Info.Step.Chain()
            chain.procs = [['internal_create_preview_extract_audio_subtitles', path, asset_guid]]
            chain.result = 0
            step.chains.append(chain)
            # Compose result
            result: Job.Result = Job.Result()
            result.handler = JobUtils.Results.cpeas.__name__
            job.results.append(result)
            return job

        @staticmethod
        def ingest_prepare(path):
            """
            Create a bunch of jobs (preview_extract_audio_subtitles), and results aggregator job
            :param path: path to source directory
            :return:
            """
            # Create final dummy job (trigger)
            agg: Job = Job()
            agg.guid.new()
            agg.name = 'Ingest: aggregate assets'
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
                job = JobUtils.CreateJob._cpeas(inp, ass)
                # TODO: add non-auto-commit connection to DBInterface, and register all jobs in single transaction
                job.status = Job.Status.INACTIVE
                # Add job to group
                job.groupIds.append(group_id)
                # Register job
                DBInterface.Job.register(job)

            # Single job's step
            # step = Job.Info.Step()
            # step.name = 'Ingest: aggregate assets'
            # chain = Job.Info.Step.Chain()
            # chain.procs = [['internal_ingest_assets', base64.b64encode(pickle.dumps(assets))]]
            # step.chains.append(chain)
            # agg.info.steps.append(step)
            res = Job.Result()
            res.handler = JobUtils.Results.assets_to_ingest.__name__
            res.actual = assets
            agg.results.append(res)
            # Register aggregator job
            DBInterface.Job.register(agg)

            # Change jobs statuses
            DBInterface.Job.set_fields_by_groups([str(group_id)], {'status': Job.Status.NEW})

        @staticmethod
        def ingest_prepare_sliced(path):
            """
            Ingest prepare step 1: filter input files, get info, capture slices
            :param path: path to source directory
            :return:
            """
            # Filter inputs: get list of all files in directory
            inputs = []
            for root, firs, files in os.walk(path):
                for f in files:
                    ne = f.rsplit('.', 1)
                    if len(ne) == 2 and ne[1] in JobUtils.ACCEPTABLE_MEDIA_FILE_EXTENSIONS:
                        inputs.append(os.path.join(root, f))
            if len(inputs) == 0:
                return

            job: Job = Job()
            job.guid.new()
            job.name = 'IPS: {}'.format(os.path.basename(path))
            job.type = Job.Type.SLICES_CREATE
            step: Job.Info.Step = Job.Info.Step()
            step.name = 'Get info, create slices'
            job.info.steps.append(step)
            chain = Job.Info.Step.Chain()
            chain.procs = [['ExecuteInternal.cpeas_slice'] + inputs]
            chain.result = 0
            step.chains.append(chain)
            # Compose result
            result = Job.Result()
            result.handler = JobUtils.Results.ingest_prepare_sliced.__name__
            job.results.append(result)
            job.status = Job.Status.NEW
            # Register job
            DBInterface.Job.register(job)

    class ResultHandlers:
        class default:
            @staticmethod
            @tracer
            def handler(r):
                # res must be a Collector.CollectedResult instance
                res = pickle.loads(base64.b64decode(r))
                pass

        class mediafile:
            @staticmethod
            def handler(mf: MediaFile):
                Logger.warning('{}\n'.format(mf.dumps(indent=2)))
                DBInterface.MediaFile.set(mf)

        class asset:
            @staticmethod
            def handler(r):
                pass

        class interaction:
            @staticmethod
            def handler(r):
                pass

        class ingest_prepare_sliced:
            @staticmethod
            def handler(r):
                # res is a list
                #     'mediafile': mf,
                #     'slices': []  # Slice data

                job_final: Job = Job()
                job_final.dependsOnGroupId.new()

                def strslice(_s):
                    return 'pattern_offset={};length={};crc={}'.format(_s['pattern_offset'], _s['length'], ','.join([str(_) for _ in _s['crc']]))

                jobs = []
                results = pickle.loads(base64.b64decode(r.actual))
                overlap = 50
                # Enumerate files
                for fi, res in enumerate(results):
                    # Mediafile is not registered yet
                    mf: MediaFile = res['mediafile']
                    mf.guid.new()
                    cdir = Storage.storage_path('cache', str(mf.guid))
                    pdir = Storage.storage_path('preview', str(mf.guid))
                    if 'slices' in res and len(res['slices']) > 0:
                        # Enumerate sliced videoTracks creating concat job for every vt
                        for vti, slices in enumerate(res['slices']):
                            vt: MediaFile.VideoTrack = mf.videoTracks[vti]
                            # Get transform setup
                            fmap = JobUtils.PIX_FMT_MAP['default'] if vt.pix_fmt not in JobUtils.PIX_FMT_MAP else JobUtils.PIX_FMT_MAP[vt.pix_fmt]
                            tmpl3 = '{c} --input - --input-depth {d} --input-csp {csp}'.format(**fmap)
                            tmpl3 += ' --input-res {w}x{h} --fps {fps}'.format(w=vt.width, h=vt.height, fps=vt.fps.val())
                            if 'P' in fmap:
                                tmpl3 += ' --profile {}'.format(fmap['P'])
                            tmpl3 += ' --allow-non-conformance --ref 3 --me umh --merange {}'.format(int(vt.width/35))
                            tmpl3 += ' --no-open-gop --keyint 30 --min-keyint 5 --rc-lookahead 30 -bframes 3 --force-flush 1'
                            bitrate = JobUtils.calc_bitrate_x265_kbps(fmap, vt.width, vt.height, vt.fps.val())
                            tmpl3 += ' --bitrate {} --vbv-maxrate {} --vbv-bufsize {}'.format(bitrate, bitrate + (bitrate >> 1), bitrate + (bitrate >> 3))
                            tmpl3 += ' --output '

                            # Create video track preview
                            preview = vt.ref_add()
                            preview.name = 'preview-video#{}'.format(vti)
                            preview.source.path = os.path.join(pdir.net_path, '{}.v{}.preview.mp4'.format(mf.guid, vti))
                            preview.source.url = '{}/{}.v{}.preview.mp4'.format(pdir.web_path, mf.guid, vti)
                            pvt:MediaFile.VideoTrack = preview.videoTracks[0]
                            #1 Create 2 concat jobs: for preview and for archive
                            job_preview_concat: Job = Job()
                            job_preview_concat.groupIds.append(job_final.dependsOnGroupId)
                            job_preview_concat.dependsOnGroupId.new()
                            job_archive_concat: Job = Job()
                            job_archive_concat.groupIds.append(job_final.dependsOnGroupId)
                            job_archive_concat.dependsOnGroupId = job_preview_concat.dependsOnGroupId
                            #2 Create Nx2 encode jobs

                            tmpl2 = 'ffmpeg -y -s {w}:{h} -r {fps} -pix_fmt {pf} -nostats -i -'.format(w=vt.width, h=vt.height, fps=vt.fps.val(), pf=vt.pix_fmt)
                            tmpl2 += ' -c:v rawvideo -f rawvideo -'
                            tmpl2 += ' -vf format=yuv420p,scale={w}:{h},blackdetect=d=0.5:pic_th=0.99:pix_th=0.005,showinfo'.format(w=pvt.width, h=pvt.height)
                            tmpl2 += ' -c:v libx264 -preset slow -g 30 -bframes 3 -refs 2 -b:v 600k '


                            segment_list_x264 = ''
                            segment_list_x265 = ''
                            pslic = None
                            for slic in res['slices'] + [None]:
                                segment_path_x264 = os.path.join(cdir.net_path, 'prv_{:03d}.h264')
                                segment_path_x265 = os.path.join(cdir.net_path, 'arch_{:03d}.hevc')
                                segment_list_x264 += 'file {}\n'.format(segment_path_x264)
                                segment_list_x265 += 'file {}\n'.format(segment_path_x265)
                                job_preview_archive_slice: Job = Job()
                                job_preview_archive_slice.groupIds.append(job_preview_concat.dependsOnGroupId)
                                result: Job.Result = Job.Result()
                                result.handler = JobUtils.Results.pa_slice.__name__

                                if slic is None:
                                    dur = vt.duration - pslic['time'] + 1
                                    proc1 = '{trim} trim --pin {pin}'.format(trim=JobUtils.TRIMMER, pin=strslice(pslic))
                                elif pslic is None:
                                    dur = slic['time'] + (overlap + slic['pattern_offset']) / vt.fps.val()
                                    proc1 = '{trim} trim --pout {pout}'.format(trim=JobUtils.TRIMMER, pout=strslice(slic))
                                else:
                                    dur = slic['time'] - pslic['time'] + (overlap + slic['pattern_offset'] - pslic['pattern_offset']) / vt.fps.val()
                                    proc1 = '{trim} trim --pin {pin} --pout {pout}'.format(trim=JobUtils.TRIMMER, pin=strslice(pslic), pout=strslice(slic))
                                if pslic is None:
                                    proc0 = 'ffmpeg -y -loglevel error -stats -i {i} -map v:{ti} -vsync 1 -r {fps} -t {t}'.format(i=mf.source.path, ti=vti, fps=vt.fps.dump_alt(), t=dur)
                                else:
                                    proc0 = 'ffmpeg -y -loglevel error -stats -ss {ss} -i {i} -map v:{ti} -vsync 1 -r {fps} -t {t}'.format(ss=pslic['time'], i=mf.source.path, ti=vti, fps=vt.fps.dump_alt(), t=dur)
                                proc0 += ' -c:v rawvideo -f rawvideo -'

                                proc1 += ' -s {} {} -p {}'.format(vt.width, vt.height, vt.pix_fmt)

                                proc2 = tmpl2 + segment_path_x264

                                proc3 = tmpl3 + segment_path_x265

                                chain: Job.Info.Step.Chain = Job.Info.Step.Chain()
                                chain.procs = [
                                    proc0.split(' '),
                                    proc1.split(' '),
                                    proc2.split(' '),
                                    proc3.split(' ')
                                ]
                                chain.progress.capture = 0
                                chain.progress.parser = 'ffmpeg_progress'

                                # Capture result from process #2
                                chain.result_capture = 2

                                step: Job.Info.Step = Job.Info.Step()
                                step.chains.append(chain)
                    # else:
                        # Create one EAS job

        class pa_slice:
            @staticmethod
            def handler(guid, r):
                # We need to obtain blacks from capture, and then update job record with it
                # r is a text like this:
                '''
                [Parsed_showinfo_1 @ 00000000046e00e0] n:   6 pts:      6 pts_time:0.2     pos:  4103859 fmt:yuv420p sar:1/1 s:1920x1080 i:P iskey:0 type:P checksum:2DE4B9FB plane_checksum:[D810410C 508326AE 91475241] mean:[46 131 125] stdev:[47.2 4.0 4.1]
                [Parsed_showinfo_1 @ 00000000046e00e0] n:   7 pts:      7 pts_time:0.233333 pos:  4110823 fmt:yuv420p sar:1/1 s:1920x1080 i:P iskey:0 type:P checksum:E545E8A2 plane_checksum:[39F4CDAB 1B68BB66 E2645F82] mean:[125 132 122] stdev:[81.3 5.3 4.4]
                [blackdetect @ 0000000004448c00] black_start:0 black_end:0.233333 black_duration:0.233333
                [Parsed_showinfo_1 @ 00000000046e00e0] n:   8 pts:      8 pts_time:0.266667 pos:  4122182 fmt:yuv420p sar:1/1 s:1920x1080 i:P iskey:0 type:P checksum:9FB49018 plane_checksum:[ADB79458 90349F08 A53C5CA9] mean:[201 131 122] stdev:[34.9 5.8 4.4]
                '''
                res = Parsers.parse_auto_text(r)
                Logger.log('{}\n'.format(pformat(res)))

        class cpeas:
            @staticmethod
            def handler(r):
                # Parse results derived from 'internal_create_preview_extract_audio_subtitles'
                res = pickle.loads(base64.b64decode(r.actual))
                DBInterface.Asset.set(res['asset'])
                for mf in res['trans'] + res['previews'] + res['archives']:
                    DBInterface.MediaFile.set(mf)
                DBInterface.MediaFile.set(res['src'])

        class assets_to_ingest:
            @staticmethod
            def handler(r):
                # Get assets from DB, merge and create Interaction
                asset_guid = None
                if len(r.actual) == 1:
                    asset_guid = r.actual[0]
                elif len(r.actual) > 1:
                    assts = DBInterface.Asset.records(r.actual)
                    assm = {}
                    for i, asst in enumerate(assts):
                        assm[str(asst['guid'])] = i
                    assets = [assts[assm[aid]] for aid in r.actual]
                    asset = merge_assets(assets)
                    asset.name = 'merged'
                    DBInterface.Asset.set(asset)
                    asset_guid = str(asset.guid)
                # Create Interaction
                inter = Interaction()
                inter.guid.new()
                inter.name = 'inter'
                inter.assetIn.set(asset_guid)
                inter.assetOut = None
                DBInterface.Interaction.set(inter)

        @staticmethod
        def process(job: Job):
            he = JobUtils.ResultHandlers.default
            try:
                he = JobUtils.ResultHandlers.__dict__[job.emitted.handler]
            except:
                pass
            for i, r in enumerate(job.emitted.results):
                hr = he
                try:
                    hr = JobUtils.ResultHandlers.__dict__[r.handler]
                except:
                    pass
                print(r.data)
                hr.handler(r.data)

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
