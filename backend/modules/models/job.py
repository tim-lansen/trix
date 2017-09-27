# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import uuid
from typing import List
from .record import *


# Result is what Task or Job emits on completion

class Task(JSONer):
    class Type:
        PROXY = 1
        ARCHIVE = 2
        PRODUCTION = 3

    def __init__(self, task_info=None):
        super().__init__()
        self.guid = Guid()
        self.jobs = None
        self.priority = None
        self.depends = None
        if task_info is None:
            # Create new task
            self.guid.new()
            self.jobs = []
            self.priority = 10
        else:
            # Update task by input data
            if type(task_info) is dict:
                self.update_json(task_info)
            else:
                self.update_str(task_info)

    def add_job(self, job):
        self.jobs.append(job)

    # def execute(self):
    #     # Queue up task's jobs
    #     pipe = self.redis.pipeline()
    #     for job_id in self.data['jobs']:
    #         pipe.smove('wait', 'cue', job_id)
    #         pipe.hset(job_id, 'phase', 'cue')
    #     pipe.execute()
    #     job_cue_signal(self.redis, self.guid)


class Job(Record):
    class Type:
        # Get info about media[, partially scan it to detect in/out/padding/...]
        PROBE        = 0x01
        # Encode video
        ENCODE_VIDEO = 0x04
        # Encode audio
        ENCODE_AUDIO = 0x08
        MUX          = 0x10
        DOWNMIX      = 0x20
        UPMIX        = 0x40
        ENCRYPT      = 0x80
        ASSEMBLE     = 0x100
        NVENC        = 0x200

        # Special types
        # This flag that tells that job is a DUMMY job that aggregates virtual 'promised' objects (uids) stored in args
        # and all that dispatcher have to do is to copy params to result, and then launch result handler
        TRIGGER = 0x0800
        # Create proxy video and audio tracks by channels, extract audio to separate tracks,
        #  scan A/V to detect in/out/padding/loudness/..., save frames info including hashes
        CPEAS = 0x8000
        PEAS = 0x8001
        EAS = 0x8002
        # Aggregate results from CPEAS
        INGEST_AGGREGATE = 0x8002
        # Create slices
        SLICES_CREATE = 0x8003
        SLICES_CONCAT = 0x8004

        # Presets:
        SIMPLE_TYPE = PROBE | ENCODE_VIDEO | ENCODE_AUDIO | MUX | DOWNMIX | UPMIX | ENCRYPT

    class Info(JSONer):
        class Aliases(JSONer):
            def __init__(self):
                super().__init__()
                # Mandatory field
                self.tmp = '/tmp'

        class Step(JSONer):
            class Chain(JSONer):
                class Progress(JSONer):
                    def __init__(self):
                        super().__init__()
                        # int: Index of process in chain to capture stderr output
                        self.capture = 0
                        # str: Name (id) of parser
                        self.parser = None
                        # float: Progress parser's output value, example: "ffmpeg_video"
                        self.pos = 0.0
                        # float: Top progress value
                        self.top = 1.0

                def __init__(self):
                    super().__init__()
                    # list(list(str)): List of processes with arguments that should be run on this chain, example:
                    # [ ["ffmpeg", "-loglevel", "error", "-stats", "-y", "-i", "${f_src}", "-t", "600", "-acodec", "pcm_s32le", "-f", "sox", "-"],
                    #   ["sox", "-t", "sox", "-", "-t", "sox", "${p_fv1}", "remix", "1v0.5,2v-0.5", "sinc", "-p", "10", "-t", "5", "100-3500", "-t", "10"] ]
                    self.procs = None
                    # list(list(int)): List of acceptable return codes for every process in self.procs
                    # len(self.return_codes) == len(self.procs), len(self.return_codes[x]) may be 0 => don't care of RC
                    # [ [0, 2], [0] ]
                    self.return_codes = None
                    # Progress class: Progress object
                    self.progress = self.Progress()

            def __init__(self):
                super().__init__()
                # (str) Step's name, example:
                # "Convert audio stereo -> 5.1"
                self.name = None
                # (list(str)) List of pipe files being created to perform job step, example:
                # ["${p_fv1}", "${p_fv2}", "${p_bv1}", "${p_bv2}", "${p_lf1}", "${p_lf2}", "${p_FLFR}", "${p_BLBR}", "${p_LFE}", "${p_FC}"]
                self.pipes: List[str] = []
                # (float) Step's weight in job - the complexity of step
                self.weight = 1.0
                # (list(Chain)) List of process chains being started in parallel by this step
                self.chains: List[Job.Info.Step.Chain] = []

        def __init__(self):
            super().__init__()
            # dict(str: str): Aliases that may be used in params or in other aliases, example:
            # { "tmp": "/tmp/${asset}",
            #   "jname": "Fox.Epic",
            #   "p_fv1": "${temp}/${jname}.fv1.sox",
            #   "p_fv2": "${temp}/${jname}.fv2.sox" }
            self.aliases = self.Aliases()
            # Names are strings that may help identify program
            self.names: List[str] = []
            # List of directories to create,
            # or list of input files for PROBE type
            self.paths: List[str] = []
            self.steps: List[Job.Info.Step] = []
            # list(MediaChunk|MediaFile): List of expected results
            # Node that executes this job should update MediaChunk or MediaFile(s) listed here
            # [
            #   {"type": "MediaChunk", "info": {"ownerId": "<uid>", "ownerIndex": "<chunk order>"}}
            # ]
            # OR
            # [
            #   {"type": "MediaFile", "info": {"guid": "<media_uid>"}},
            #   {"type": "MediaFile", "info": {"guid": "<media_proxy_uid>"}},
            #   {"type": "Asset", "info": {
            #       "guid": "<asset_uid>",
            #       "proxyId": "<asset_proxy_uid>",
            #       "streams": [
            #           {"source": {"mediaFileId": "<media_uid>", "streamKind": "VIDEO", "streamKindIndex": 0}},
            #           {"destination": {"streamKind": "VIDEO"}}
            #       ]
            #   }},
            #   {"type": "Asset", "info": {
            #       "guid": "<asset_proxy_uid>",
            #       "streams": [
            #           {"source": {"mediaFileId": "<media_proxy_uid>", "streamKind": "VIDEO", "streamKindIndex": 0}},
            #           {"destination": {"streamKind": "VIDEO"}}
            #       ]
            #   }}
            # ]
            # OR
            # [
            #   {"type": "MediaFile", "info": {"guid": "<media_uid>"}},
            #   {"type": "MediaFile", "info": {"guid": "<media_proxy_uid0>"}},
            #   {"type": "MediaFile", "info": {"guid": "<media_proxy_uid1>"}},
            #   {"type": "Asset", "info": {
            #       "guid": "<asset_uid>",
            #       "streams": [
            #           {"source": {"mediaFileId": "<media_uid>", "streamKind": "AUDIO", "streamKindIndex": 0}},
            #           {"destination": {"streamKind": "VIDEO"}}
            #       ]
            #   }}
            # ]
            # self.results: List[Job.Result] = []

        def max_parallel_chains(self):
            """
            Expose maximum parallel chains that require to pass final results
            :return: int
            """
            return max([len(s.chains) for s in self.steps]) if len(self.steps) else 0

    class Status:
        INACTIVE = 0
        NEW = 1
        WAITING = 2
        OFFERED = 3
        EXECUTING = 4
        FINISHED = 5
        FAILED = 6
        CANCELED = 7

    class Emitted(JSONer):
        class Result(JSONer):
            class Source(JSONer):
                def __init__(self):
                    super().__init__()
                    # Address of text source to capture
                    self.step = 0
                    self.chain = 0
                    self.proc = 0
                    self.parser = None

            def __init__(self):
                super().__init__()
                # Data source address
                self.source = self.Source()
                # Parsed data
                self.data = None
                # Result handler (member function of JobUtils.ResultHandlers)
                self.handler = None

        # class CollectorId(Guid):
        #     def __init__(self):
        #         super().__init__()

        def __init__(self, jobId: Guid):
            super().__init__()
            self.jobId = jobId
            # Results handler procedure (member function of JobUtils.ResultHandlers)
            self.handler = None
            # Aggregating collector's id
            # self.collectorId = self.CollectorId()
            # List of job results
            self.results: List[self.Result] = []

    # Guid type support class
    class GroupId(Guid):
        def __init__(self):
            super().__init__()

    def update_json(self, json_obj):
        super().update_json(json_obj)
        self.emitted.jobId = self.guid

    def update_str(self, json_str):
        super().update_str(json_str)
        self.emitted.jobId = self.guid

    class DependsOnGroupId(Guid):
        def __init__(self):
            super().__init__()

    def __init__(self, name=None, guid=None):
        super().__init__(name, guid)
        self.type = None
        self.info = Job.Info()
        self.fails = 0
        self.offers = 0
        self.status = self.Status.NEW
        self.priority = 0
        # float: Overall job progress, 0.0 at start, 1.0 at end
        self.progress = 0.0
        # List of groups that this job belongs to
        self.groupIds: List[Guid] = []
        # This job depends on jobs from group <dependsOnGroupId>, independent if self.dependsOnGroupId.is_null()
        self.dependsOnGroupId = self.DependsOnGroupId()
        # Condition is a pythonic expression that can be evaluated in job's context???
        self.condition = None

        # Job results
        self.emitted: Job.Emitted = Job.Emitted(self.guid)

    # Table description
    TABLE_SETUP = {
        "relname": "trix_jobs",
        # Each job may depend on group, and/or have launch condition
        # taskId: uid of parent task
        # groupId: uid of group, it's being assigned when creating a group dependent job
        # depends: uid of group of jobs that must be finished before this job is started
        "fields": [
            ["type", "integer NOT NULL"],
            ["info", "json NOT NULL"],
            ["fails", "integer NOT NULL"],
            ["offers", "integer NOT NULL"],
            ["status", "integer NOT NULL"],
            ["priority", "integer NOT NULL"],
            ["progress", "double precision"],
            ["groupIds", "uuid[]"],
            ["dependsOnGroupId", "uuid"],
            ["condition", "json"],
            ["emitted", "json"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }


def test() -> Job:
    job: Job = Job()
    job_obj = {
        "guid": str(uuid.uuid4()),
        "name": "Test job: downmix",
        "type": Job.Type.DOWNMIX,
        "info": {
            "aliases": {
                # Temporary folder
                "tmp": "/tmp/slot00",
                "alias": "Disney.Frozen",
                "f_src": "/mnt/server1_id/crude/in_work/avatar_audio_stereo.mp4",
                "f_dst": "${previews}/${new_media_id}/avatar_audio_downmix.mp4",
                "asset_id": "49cf7a5b-02ed-453a-8562-32c5b34d471a",
                "new_media_id": "1122334455667788",
                "previews": "/mnt/server1_id/web/preview"
            },
            # Folders to be created before start processing
            "paths": [
                "${tmp}/pipes",
                "${previews}/${new_media_id}"
            ],
            "steps": [
                {
                    "name": "Downmix audio stereo -> mono",
                    "weight": 0.999,
                    "chains": [
                        {
                            "procs": [
                                "ffmpeg -y -loglevel error -i ${f_src} -t 600 -c:a pcm_s32le -f sox -".split(' '),
                                "sox -t sox - -t sox - remix 1v0.5,2v0.5 sinc -p 10 -t 5 100-3500 -t 10".split(' '),
                                "ffmpeg -y -loglevel error -stats -f sox -i - -c:a aac -strict -2 -b:a 64k ${f_dst}".split(' ')
                            ],
                            "return_codes": [[0, 2], [0], [0]],
                            "progress": {
                                "capture": 2,
                                "parser": "ffmpeg_progress",
                                "top": 600.0
                            }
                        }
                    ]
                },
                {
                    "name": "Combined Info",
                    "weight": 0.001,
                    "chains": [
                        {
                            "procs": [
                                ["ExecuteInternal.combined_info", "{}", "${f_dst}"]
                            ]
                        }
                    ]
                }
            ]
        },
        "emitted": {
            "results": [
                {
                    "source": {
                        "step": 1
                    },
                    "handler": "mediafile",
                }
            ]
        }
    }
    job.groupIds.append(Guid())
    job.groupIds.append(Guid(0))
    job.update_json(job_obj)
    # print(job.dumps(indent=2))
    return job
