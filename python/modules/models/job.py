# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import uuid
from typing import List
from .record import *


class JobStatus:
    NEW = 1
    WAITING = 2
    OFFERED = 3
    EXECUTING = 4
    FINISHED = 5
    FAILED = 6


class JobType:
    PROBE = 1
    PROXY = 2
    ARCHIVE = 3
    PRODUCTION = 4


class Task(JSONer):
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
            # str: Asset UIDs
            self.src_asset = None
            self.dst_asset = None
            # dict(str: str): List of variables that may be used in params or in other variables, example:
            # { "temp": "/tmp/${asset}",
            #   "jname": "Fox.Epic",
            #   "p_fv1": "${temp}/${jname}.fv1.sox",
            #   "p_fv2": "${temp}/${jname}.fv2.sox" }
            self.variables = None
            self.steps: List[Job.Info.Step] = []

    def __init__(self):
        super().__init__()
        self.info = Job.Info()
        self.type = None
        self.status = None
        # float: Overall job progress, 0.0 at start, 1.0 at end
        self.progress = 0.0
        self.condition = None

    def update(self, job_data):
        # if type(job_data) is list or type(job_data) is tuple:
        #     # The variant for data captured from database (dangerous)
        #     # Create dict
        #     fields = [f[0] for f in TRIX_CONFIG.dbase.tables['Job']['fields']]
        #     upd = dict(zip(fields, job_data))
        #     self.update_json(upd)
        if type(job_data) is dict:
            self.update_json(job_data)
        else:
            self.update_str(job_data)



# def create_record(r, name, hdict, rtype, keyset=None):
#     # 'keyset' is name of set accumulating names of hashes being created
#     s, m = r.time()
#     t = float(s) + float(m)/1000000.0
#     hdict.update({
#         'type' : rtype,
#         'ctime': t,
#         'mtime': t
#     })
#     pipe = r.pipeline()
#     pipe.hmset(name, hdict)
#     if keyset:
#         pipe.sadd(keyset, name)
#     pipe.execute()
#     return True
#
#
# def update_record(r, name, hdict):
#     s, m = r.time()
#     t = float(s) + float(m)/1000000.0
#     hdict.update({'mtime': t})
#     r.hmset(name, hdict)


JOB_PHASES = ['wait', 'cue', 'offered', 'process', 'finished', 'failed']
