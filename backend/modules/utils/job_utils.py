# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import re
import os
import json
import uuid
import pickle
import base64
from typing import List
from modules.models.job import Job
from modules.models.asset import Asset, Stream
from modules.models.interaction import Interaction
from modules.utils.database import DBInterface
from .log_console import Logger


def merge_assets(assets):
    # def _advance_stream(_s: Stream, _i):
    #     for _ch in _s.channels:
    #         _ch.src_stream_index += _i

    def _advance_streams(_ss: List[dict], _i):
        _ass = []
        if _ss is not None and len(_ss) > 0:
            for _s in _ss:
                _ass.append(_s)
                for _ch in _s['channels']:
                    _ch['src_stream_index'] += _i
        return _ass

    asset = Asset()
    asset.guid.new()
    vii = 0
    aii = 0
    sii = 0
    for a in assets:
        # a = Asset()
        # a.update_json(axaxa)
        # print(a.dumps(indent=2))

        vss = _advance_streams(a['videoStreams'], vii)
        vii += len(vss)
        ass = _advance_streams(a['audioStreams'], aii)
        aii += len(ass)
        sss = _advance_streams(a['subStreams'], sii)
        sii += len(sss)

        asset.videoStreams += vss
        asset.audioStreams += ass
        asset.subStreams += sss
        asset.mediaFiles += a['mediaFiles']

    return asset


class JobUtils:
    ACCEPTABLE_MEDIA_FILE_EXTENSIONS = {
        'm2ts', 'm2v', 'mov', 'mkv', 'mp4', 'mpeg', 'mpg', 'mpv',
        'mts', 'mxf', 'webm', 'ogg', 'gp3', 'avi', 'vob', 'ts',
        '264', 'h264',
        'flv', 'f4v', 'wav', 'ac3', 'aac', 'mp2', 'mp3', 'mpa',
        'sox', 'dts', 'dtshd'
    }

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
            job = Job()
            job.type = Job.Type.PROBE
            job.info.names = names
            job.info.aliases['base'] = base
            step = Job.Info.Step()
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
                    [
                        'internal_combined_info',
                        '{"guid":"${{{}}}"}'.format(uidn),
                        '${{{}}}'.format(srcn)
                    ]
                ]
                chain.result = 0
                step.chains.append(chain)
                # Compose result
                result = Job.Info.Result()
                result.type = Job.Info.Result.Type.MEDIAFILE
                result.predefined = {"guid": '${{{}}}'.format(uidn), "source": {"url": '${{{}}}'.format(srcn)}}
                job.info.results.append(result)
            # Register job
            DBInterface.Job.register(job)
            return job

        @staticmethod
        def _cpeas(path, asset_guid):
            job = Job()
            job.guid.new()
            job.name = 'CPEAS: {}'.format(os.path.basename(path))
            job.type = Job.Type.CPEAS
            step = Job.Info.Step()
            step.name = 'Create proxy, extract audio and subtitles'
            job.info.steps.append(step)
            chain = Job.Info.Step.Chain()
            chain.procs = [['internal_create_preview_extract_audio_subtitles', path, asset_guid]]
            chain.result = 0
            step.chains.append(chain)
            # Compose result
            result = Job.Info.Result()
            result.type = Job.Info.Result.Type.CPEAS
            job.info.results.append(result)
            return job

        @staticmethod
        def create_preview_extract_audio_subtitles(path):
            """
            Create a job that performs 'internal_create_preview_extract_audio_subtitles' on the <path>
            :param path: path to AV file
            :return: job
            """
            job = JobUtils.CreateJob._cpeas(path)
            # Register job
            DBInterface.Job.register(job)
            return job

        @staticmethod
        def ingest_prepare(path):
            """
            Create a bunch of jobs (preview_extract_audio_subtitles), and results aggregator job
            :param path: path to source directory
            :return:
            """
            # Create final dummy job (trigger)
            agg = Job()
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
            res = Job.Info.Result()
            res.type = Job.Info.Result.Type.ASSETS_TO_INGEST
            res.actual = assets
            agg.info.results.append(res)
            # Register aggregator job
            DBInterface.Job.register(agg)

            # Change jobs statuses
            DBInterface.Job.set_fields_by_groups([str(group_id)], {'status': Job.Status.NEW})

    class Results:
        @staticmethod
        def _undefined(r):
            pass

        def _mediafile(r):
            mf = pickle.loads(base64.b64decode(r.actual))
            DBInterface.MediaFile.set(mf.dumps())

        def _asset(r):
            pass

        def _interaction(r):
            pass

        def _cpeas(r):
            # Parse results derived from 'internal_create_preview_extract_audio_subtitles'
            res = pickle.loads(base64.b64decode(r.actual))
            DBInterface.Asset.set(res['asset'])
            for mf in res['trans'] + res['previews'] + res['archives']:
                DBInterface.MediaFile.set(mf)

        def _assets_to_ingest(r):
            # Get assets from DB, merge and create Interaction
            if len(r.actual) == 1:
                auid = r.actual[0]
            elif len(r.actual) > 1:
                assets = DBInterface.Asset.records(r.actual)
                asset = merge_assets(assets)
                asset.name = 'merged'
                DBInterface.Asset.set(asset)
                auid = str(asset.guid)
            # Create Interaction
            inter = Interaction()
            inter.guid.new()
            inter.name = 'inter'
            inter.assetIn.set(auid)
            inter.assetOut = None
            DBInterface.Interaction.set(inter)

        Vectors = {
            Job.Info.Result.Type.MEDIAFILE:     _mediafile,
            Job.Info.Result.Type.ASSET:         _asset,
            Job.Info.Result.Type.INTERACTION:   _interaction,
            Job.Info.Result.Type.CPEAS:         _cpeas,
            Job.Info.Result.Type.ASSETS_TO_INGEST: _assets_to_ingest,
            Job.Info.Result.Type.FILE:          _undefined,
            Job.Info.Result.Type.TASK:          _undefined,
            Job.Info.Result.Type.JOB:           _undefined,
            # Reactive result type:
            Job.Info.Result.Type.HOOK_ARCHIVE:  _undefined,
        }

        def process(self, results: List[Job.Info.Result]):
            for r in results:
                t = r.type & (0x7FFFFFFF ^ Job.Type.TRIGGER)
                if t in self.Vectors:
                    self.Vectors[t](r)
                else:
                    self._undefined(r)

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

    if 'JobUtils' not in globals() or 'RESULTS' not in globals()['JobUtils'].__dict__:
        RESULTS = Results()
