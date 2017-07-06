# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import re
import uuid
import json
from typing import List
from .record import *


class Task(JSONer):
    class Type:
        PROXY = 1
        ARCHIVE = 2
        PRODUCTION = 3

    def __init__(self, task_info=None):
        super().__init__()
        self.id = None
        self.jobs = None
        self.priority = None
        self.depends = None
        if task_info is None:
            # Create new task
            self.id = str(uuid.uuid4())
            self.jobs = []
            self.priority = 10
        else:
            # Update task by input data
            if type(task_info) is dict:
                self.update_json(task_info)
            else:
                self.update_str(task_info)

    # def update(self):
    #     update_record(self.redis, self.id, self.data)

    def add_job(self, job):
        self.jobs.append(job)
        #self.data['jobs'].append(job.id)

    # def execute(self):
    #     # Queue up task's jobs
    #     pipe = self.redis.pipeline()
    #     for job_id in self.data['jobs']:
    #         pipe.smove('wait', 'cue', job_id)
    #         pipe.hset(job_id, 'phase', 'cue')
    #     pipe.execute()
    #     job_cue_signal(self.redis, self.id)


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

    class Status:
        NEW = 1
        WAITING = 2
        OFFERED = 3
        EXECUTING = 4
        FINISHED = 5
        FAILED = 6

    class Info(JSONer):
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
                        self.top = None

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
                self.pipes = None
                # (float) Step's weight in job - the complexity of step
                self.weight = 1.0
                # (list(Chain)) List of process chains being started in parallel by this step
                self.chains: List[Job.Info.Step.Chain] = []

        def __init__(self):
            super().__init__()
            # dict(str: str): Aliases that may be used in params or in other aliases, example:
            # { "temp": "/tmp/${asset}",
            #   "jname": "Fox.Epic",
            #   "p_fv1": "${temp}/${jname}.fv1.sox",
            #   "p_fv2": "${temp}/${jname}.fv2.sox" }
            self.aliases = None
            # List of directories to create
            self.paths: List[str] = []
            self.steps: List[Job.Info.Step] = []
            # list(MediaChunk|MediaFile): List of expected results
            # Node that executes this job should update MediaChunk or MediaFile(s) listed here
            # [
            #   {"type": "MediaChunk", "info": {"ownerId": "<uid>", "ownerIndex": "<chunk order>"}}
            # ]
            # OR
            # [
            #   {"type": "MediaFile", "info": {"id": "<media_uid>"}},
            #   {"type": "MediaFile", "info": {"id": "<media_proxy_uid>"}},
            #   {"type": "Asset", "info": {
            #       "id": "<asset_uid>",
            #       "proxyId": "<asset_proxy_uid>",
            #       "streams": [
            #           {"source": {"mediaFileId": "<media_uid>", "streamKind": "VIDEO", "streamKindIndex": 0}},
            #           {"destination": {"streamKind": "VIDEO"}}
            #       ]
            #   }},
            #   {"type": "Asset", "info": {
            #       "id": "<asset_proxy_uid>",
            #       "streams": [
            #           {"source": {"mediaFileId": "<media_proxy_uid>", "streamKind": "VIDEO", "streamKindIndex": 0}},
            #           {"destination": {"streamKind": "VIDEO"}}
            #       ]
            #   }}
            # ]
            # OR
            # [
            #   {"type": "MediaFile", "info": {"id": "<media_uid>"}},
            #   {"type": "MediaFile", "info": {"id": "<media_proxy_uid0>"}},
            #   {"type": "MediaFile", "info": {"id": "<media_proxy_uid1>"}},
            #   {"type": "Asset", "info": {
            #       "id": "<asset_uid>",
            #       "streams": [
            #           {"source": {"mediaFileId": "<media_uid>", "streamKind": "AUDIO", "streamKindIndex": 0}},
            #           {"destination": {"streamKind": "VIDEO"}}
            #       ]
            #   }}
            # ]
            self.results = None

    def __init__(self):
        super().__init__()
        self.info = self.Info()
        self.type = None
        self.status = self.Status.NEW
        self.priority = 0
        self.fails = 0
        self.offers = 0
        # float: Overall job progress, 0.0 at start, 1.0 at end
        self.progress = 0.0
        self.condition = None
        self.depends = None
        self.results = None


def test() -> Job:
    job = Job()
    job_obj = {
        # "id": "3631f021-8dd0-4197-a29d-27fc3180a242",
        "name": "Test job",
        "type": Job.Type.DOWNMIX,
        "info": {
            "aliases": {
                "src_asset": "f22ba38e-7c50-4760-81c9-d8b3a4724fc1",
                "dst_asset": "f22ba38e-7c50-4760-81c9-d8b3a4724fc3",
                "temp": "C:/temp/${dst_asset}",
                "alias": "Disney.Frozen",
                "f_src": "F:/music/The Art Of Noise/1987 - In No Sence - Nonsence!/15 - Crusoe.mp3",
                "f_dst": "F:/temp/test.sox",
                "new_media_id": "b0db8575-94b2-4202-804e-6cbda0ff5ee3",
                "asset_id": "49cf7a5b-02ed-453a-8562-32c5b34d471a"
            },
            "results": [
                {"type": "MediaFile", "info": {"id": "${new_media_id}", "source": {"url": "${f_dst}"}}},
                {"type": "Asset", "info": {"id": "${asset_id}", "streams": [
                    {
                        "source": {"mediaFileId": "${new_media_id}", "streamKind": "AUDIO", "streamKindIndex": 0},
                        "destination": {"streamKind": "AUDIO", "streamKindIndex": 0, "channelIndex": 0}
                    }
                ]}}
            ],
            "steps": [
                {
                    "name": "Convert audio stereo -> 5.1",
                    "weight": 1.0,
                    "chains": [
                        {
                            "procs": [
                                ["ffmpeg", "-y", "-i", "${f_src}", "-c:a", "pcm_s32le", "-f", "sox", "-"],
                                ["sox", "-t", "sox", "-", "-t", "sox", "${f_dst}", "remix", "1v0.5,2v-0.5", "sinc", "-p", "10", "-t", "5", "100-3500", "-t", "10"]
                            ],
                            "return_codes": [[0, 2], [0]],
                            "progress": {
                                "capture": 0,
                                "parser": "ffmpeg",
                                "top": 600.0
                            }
                        }
                    ]
                }
            ]
        }
    }
    job.update_json(job_obj)
    # print(job.dumps(indent=2))
    return job
