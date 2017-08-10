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

    # def update(self):
    #     update_record(self.redis, self.guid, self.data)

    def add_job(self, job):
        self.jobs.append(job)
        #self.data['jobs'].append(job.guid)

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
        # Create proxy video and audio tracks by channels, extract audio to separate tracks,
        #  scan A/V to detect in/out/padding/loudness/..., save frames info including hashes
        CREATE_PROXY = 0x02
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
                        self.done = 0.0
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
                    # Chain result, may be used to store result of internal procs
                    self.result = None

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

        class Result(JSONer):
            class Type:
                UNDEFINED = 0
                MEDIAFILE = 1
                ASSET = 2
                INTERACTION = 3
                COMBINED_INFO = 4
                FILE = 5
                TASK = 6
                JOB = 7
                # Reactive result type:
                HOOK_ARCHIVE = 8

            def __init__(self):
                super().__init__()
                self.type = 0
                # Bulk object (by type):
                # MEDIAFILE: MediaFile object with URL set to newly created media file
                # ASSET: ...
                # INTERACTION: Interaction object
                self.predefined = None
                # Expected base object, any params may be set
                # for example, it may be MediaFile() with one VideoTrack, and
                #  mf.videoTracks[0].par = Rational(1, 1)
                #  mf.videoTracks[0].pix_fmt = 'yuv420p'
                # self.expected = None
                # Actual result object
                # for example, it may be MediaFile() derived from combined_info(mf, url)
                self.actual = None
                self.index = None

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
            self.results: List[Job.Info.Result] = []

        def max_parallel_chains(self):
            """
            Expose maximum parallel chains that require to pass final results
            :return: int
            """
            mpc = 0
            for s in self.steps:
                if [_.result is not None for _ in s.chains].count(True):
                    mpc = max(mpc, len(s.chains))
            return mpc

    class Status:
        NEW = 1
        WAITING = 2
        OFFERED = 3
        EXECUTING = 4
        FINISHED = 5
        FAILED = 6
        CANCELED = 7

    # Guid type support class
    class GroupId(Guid):
        def __init__(self):
            super().__init__()

    def __init__(self):
        super().__init__()
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
        self.dependsOnGroupId = Guid()
        # Condition is a pythonic expression that can be evaluated in job's context???
        self.condition = None

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
            # ["results", "json"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }


def test() -> Job:
    job = Job()
    job_obj = {
        "guid": str(uuid.uuid4()),
        "name": "Test job",
        "type": Job.Type.DOWNMIX,
        "info": {
            "aliases": {
                # "src_asset": "f22ba38e-7c50-4760-81c9-d8b3a4724fc1",
                # "dst_asset": "f22ba38e-7c50-4760-81c9-d8b3a4724fc3",
                # "temp": "C:/temp/${dst_asset}",
                "alias": "Disney.Frozen",
                "f_src": "/mnt/server1_id/crude/in_work/test_eng1_20.mp4",
                "f_dst": "/mnt/server1_id/web/preview/test_eng1_downmix.mp4",
                "new_media_id": str(uuid.uuid4()),
                "asset_id": "49cf7a5b-02ed-453a-8562-32c5b34d471a"
            },
            "steps": [
                {
                    "name": "Convert audio stereo -> 5.1",
                    "weight": 1.0,
                    "chains": [
                        {
                            "procs": [
                                "ffmpeg -y -i ${f_src} -c:a pcm_s32le -f sox -".split(' '),
                                "sox -t sox - -t sox - remix 1v0.5,2v-0.5 sinc -p 10 -t 5 100-3500 -t 10".split(' '),
                                "ffmpeg -y -f sox -i - -c:a aac -strict -2 -b:a 64k ${f_dst}".split(' ')
                            ],
                            "return_codes": [[0, 2], [0], [0]],
                            "progress": {
                                "capture": 2,
                                "parser": "ffmpeg",
                                "top": 600.0
                            }
                        }
                    ]
                }
            ],
            "results": [
                {"type": "MediaFile", "info": {"guid": "${new_media_id}", "source": {"url": "${f_dst}"}}},
                # {"type": "Asset", "info": {"guid": "${asset_id}", "streams": [
                #     {
                #         "source": {"mediaFileId": "${new_media_id}", "streamKind": "AUDIO", "streamKindIndex": 0},
                #         "destination": {"streamKind": "AUDIO", "streamKindIndex": 0, "channelIndex": 0}
                #     }
                # ]}}
            ]
        }
    }
    job.groupIds.append(Guid())
    job.groupIds.append(Guid(0))
    job.update_json(job_obj)
    # print(job.dumps(indent=2))
    return job

