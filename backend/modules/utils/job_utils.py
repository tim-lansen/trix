# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import re
import os
import json
import uuid
from typing import List
from modules.models.job import Job
from modules.utils.database import DBInterface
from .log_console import Logger


class JobUtils:
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

    class Results:
        @staticmethod
        def _undefined(r):
            pass

        def _mediafile(r):
            DBInterface.MediaFile.set(r.actual)

        def _asset(r):
            pass

        def _interaction(r):
            pass

        Vectors = {
            Job.Info.Result.Type.MEDIAFILE:     _mediafile,
            Job.Info.Result.Type.ASSET:         _asset,
            Job.Info.Result.Type.INTERACTION:   _interaction,
            Job.Info.Result.Type.FILE:          _undefined,
            Job.Info.Result.Type.TASK:          _undefined,
            Job.Info.Result.Type.JOB:           _undefined,
            # Reactive result type:
            Job.Info.Result.Type.HOOK_ARCHIVE:  _undefined,
        }

        def process(self, results: List[Job.Info.Result]):
            for r in results:
                if r.type in self.Vectors:
                    self.Vectors[r.type](r)
                else:
                    self._undefined(r)

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
