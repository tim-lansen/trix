# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


# The job execution engine
# It takes a Job, executes it, and process results
# Scenario 1:
# - customer creates a bulk MediaFile object, bulk.source.url = src_url;
# - customer creates a job with type = PROBE, steps = [] and results = [{'type': MEDIAFILE, 'bulk': bulk}, {'type': }]

import os
import sys
import time
import json
import uuid
import pickle
import base64
import shutil
from copy import deepcopy
from typing import List
from multiprocessing import Process, Event, Queue
# import queue
from modules.models.job import Job
from modules.models.interaction import Interaction
from modules.utils.log_console import Logger, tracer
from .parsers import PARSERS, parse_text, timecode_to_float
from .execute_chain import execute_chain
from .cross_process_lossy_queue import CPLQueue
from .job_utils import JobUtils

from modules.models.mediafile import MediaFile
from .combined_info import combined_info


class JobExecutor:
    class Execution:

        def __init__(self):
            self.job: Job = None
            self.progress_output = CPLQueue(5)
            # This queue is used to pass results of internal procedures from execute_chain
            # Note that this king of job may have only 1 step with 1 single-proc chain
            # self.final = CPLQueue(2)
            self.finals: List[CPLQueue] = []
            self.fmap = {}
            self.fmap_out = Queue()
            self.error = Event()
            self.finish = Event()
            self.running = Event()
            self.force_exit = Event()

        @staticmethod
        def _hash(si, ci, pi):
            return '{:02d}.{:02d}.{:02d}'.format(si, ci, pi)

        def final_register(self, step, chain, proc):
            hash = self._hash(step, chain, proc)
            self.fmap[hash] = None

        def final_set(self, step, chain, proc, obj):
            hash = self._hash(step, chain, proc)
            if hash in self.fmap:
                self.fmap[hash] = obj

        def final_get(self, step, chain, proc):
            hash = self._hash(step, chain, proc)
            return self.fmap[hash] if hash in self.fmap else None

        @tracer
        def reset(self, finals_count=0):
            self.progress_output.flush('reset')
            for f in self.finals:
                f.flush('reset')
            if len(self.finals) < finals_count:
                self.finals += [CPLQueue(2) for _ in range(finals_count - len(self.finals))]
            self.fmap.clear()
            self.error.clear()
            self.finish.clear()
            self.running.clear()
            self.force_exit.clear()
            # self.job = None

    def __init__(self):
        self.exec = JobExecutor.Execution()
        self.process: Process = None
        self._last_captured_progress = 0.0

    @staticmethod
    def _process(ex: Execution):
        ex.running.set()
        # if ex.job.type & Job.Type.TRIGGER:
        #     Logger.info("Dummy job (trigger) {}\n".format(ex.job.name))
        #     ex.finish.set()
        #     return
        chain_enter = Event()
        chain_error = Event()
        try:
            Logger.info("Starting job {}\n".format(ex.job.name))
            # Register finals
            for r in ex.job.emitted.results:
                ex.final_register(r.source.step, r.source.chain, r.source.proc)
            # Prepare paths
            for path in ex.job.info.paths:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                os.makedirs(path)
            for ai, step in enumerate(ex.job.info.steps):
                Logger.info("Step #{}\n".format(ai))
                # Prepare pipes
                for pipe in step.pipes:
                    os.mkfifo(pipe)
                step_queues = [CPLQueue(5) for _ in step.chains]
                # monitors: List[Job.Info.Step.Chain.Progress] = []
                threads: List[Process] = []

                # Initialize and start step's chains execution, each chain in own thread
                for ci, chain in enumerate(step.chains):
                    # Workaround Python's bad threading
                    if len(threads):
                        time.sleep(1.0)
                    q_fin = ex.finals[ci]
                    # queues = [CPLQueue(5) for _ in chain.procs]
                    # EDIT: capture only proc set as progress
                    q_pro = step_queues[ci]
                    t = Process(target=execute_chain, args=(chain, q_pro, q_fin, chain_enter, chain_error))
                    t.start()
                    threads.append(t)
                    chain_enter.wait()
                    chain_enter.clear()

                # Wait step to finish
                while True:
                    if [t.is_alive() for t in threads].count(True) == 0:
                        break
                    # Compile info from chains
                    for ci, q_pro in enumerate(step_queues):
                        c = q_pro.flush('step')
                        if c is None:
                            continue
                        cap = pickle.loads(base64.b64decode(c))
                        if 'time' in cap:
                            step.chains[ci].progress.pos = timecode_to_float(cap['time'])
                    # calculate step progress
                    step_progress = 0.0
                    for chain in step.chains:
                        step_progress += chain.progress.pos/chain.progress.top
                    job_progress = step_progress / (len(step.chains) * len(ex.job.info.steps))
                    ex.progress_output.put('{{"step":{},"progress":{:.3f}}}'.format(ai, job_progress))
                    time.sleep(0.5)

                # Step is finished, cleaning up
                for chain in step.chains:
                    chain.progress.pos = 1.0
                for pipe in step.pipes:
                    os.remove(pipe)
                if chain_error.is_set():
                    chain_error.clear()
                    Logger.error("Job failed on step {}\n".format(ai))
                    ex.error.set()
                    break
                # Collect finals
                for ci, q_fin in enumerate(ex.finals):
                    try:
                        cap = pickle.loads(base64.b64decode(q_fin.get()))
                        for pi, text in enumerate(cap):
                            ex.final_set(ai, ci, pi, text)
                    except Exception as e:
                        Logger.critical('{}\n'.format(e))
                        Logger.traceback()
                Logger.info("Step {} finished\n".format(ai))
                ex.progress_output.put('{{"step":{},"progress":{:.3f}}}'.format(ai, (ai + 1.0)/len(ex.job.info.steps)))
            Logger.info("Job finished\n")
        except Exception as e:
            Logger.error("Job failed: {}\n".format(e))
            Logger.traceback()
            Logger.warning('{}\n'.format(ex.job.dumps()))
            ex.error.set()
        ex.running.clear()
        ex.fmap_out.put(base64.b64encode(pickle.dumps(ex.fmap)))
        # Set finish event only if no error
        if not ex.error.is_set():
            ex.finish.set()

    def results(self):
        self.exec.fmap.clear()
        try:
            self.exec.fmap = pickle.loads(base64.b64decode(self.exec.fmap_out.get()))
        except Exception as e:
            Logger.critical('{}\n'.format(e))
            Logger.traceback()
        if self.exec.job.emitted is None or len(self.exec.job.emitted.results) == 0:
            Logger.warning('No results to emit\n')
            return None
        # if self.exec.job.type & Job.Type.TRIGGER:
        #     Logger.info("Dummy job results\n")
        #     JobUtils.Results.process(self.exec.job)
        #     return len(self.exec.job.results)

        rc = 0
        for result in self.exec.job.emitted.results:
            text = self.exec.final_get(result.source.step, result.source.chain, result.source.proc)
            result.data = parse_text(text, result.source.parser)
            rc += 1
        JobUtils.Results.process(self.exec.job)
        return rc

    def working(self):
        return self.process and self.process.is_alive()

    def progress(self):
        cap = self.exec.progress_output.flush('JobExecutor.progress')
        if cap is not None:
            jcap = json.loads(cap)
            Logger.log('{}\n'.format(jcap))
            self._last_captured_progress = jcap['progress']
        return self._last_captured_progress

    def run(self, job: Job):
        if self.process:
            if self.process.is_alive():
                Logger.error("JobExecutor.run: process is alive!\n")
                return False
            self.process = None

        self.exec.job = job
        self.exec.reset(job.info.max_parallel_chains())

        # If job is trigger type, do not start it
        if job.type & Job.Type.TRIGGER:
            Logger.info("Dummy job (trigger) {}\n".format(job.name))
            self._last_captured_progress = 1.0
            self.exec.finish.set()
            return True

        JobUtils.resolve_aliases(job)
        self._last_captured_progress = 0.0
        self.process = Process(target=JobExecutor._process, args=(self.exec,))
        self.process.start()
        self.exec.running.wait(timeout=10.0)
        if self.exec.running.is_set():
            Logger.info("Job execution started\n")
            return True
        Logger.error("Failed to start job execution\n")
        self.process.terminate()
        self.process = None
        return False

    def stop(self):
        if self.process:
            if self.process.is_alive():
                self.exec.force_exit.set()
                self.process.join(timeout=8)
                if self.process.is_alive():
                    Logger.error("Terminating process\n")
                    self.process.terminate()


def test():
    job = Job()
    job.update_json({
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
                    "weight": 1.0,
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
                }
            ],
            "results": [
                {"handler": JobUtils.Results.mediafile, "info": {"guid": "${new_media_id}", "source": {"url": "${f_dst}"}}}
            ]
        }
    })
    job_executor = JobExecutor()
    job_executor.run(job)
    working = True
    while working:
        # Listen to individual channel, timeout-blocking when finishing
        if job_executor.exec.error.is_set():
            Logger.critical('job {} failed\n'.format(job.guid))
            job_executor.exec.reset()
            break
        if job_executor.exec.finish.is_set():
            Logger.info('job {} finished\n'.format(job.guid))
            break

        Logger.log('Job progress: {}\n'.format(job_executor.progress()))
        working = job_executor.working()
        time.sleep(1)

    job_executor.stop()


def test_combined_info():
    job = Job()
    job.update_json({
        "guid": str(uuid.uuid4()),
        "name": "Get combined info",
        "type": Job.Type.PROBE,
        "info": {
            "aliases": {
                "server1": "/mnt/server1_id",
                "src0": "${server1}/crude/in_work/test_eng1_20.mp4",
                "src1": "${server1}/crude/in_work/39f8a04c1b6ee9d3c60650c8ed80eb.768x320.600k.AV.mp4",
                "mf0": str(uuid.uuid4()),
                "mf1": str(uuid.uuid4())
            },
            "steps": [
                {
                    "name": "combined info",
                    "chains": [
                        {
                            "procs": ['internal_combined_info {"guid":"${mf0}"} ${src0}'.split(' ')],
                            "result": 0     # Anything but None
                        },
                        {
                            "procs": ['internal_combined_info {"guid":"${mf1}"} ${src1}'.split(' ')],
                            "result": 0  # Anything but None
                        }
                    ]
                }
            ],
            "results": [
                {"handler": JobUtils.Results.mediafile, "predefined": {"guid": "${mf0}", "source": {"url": "${src0}"}}},
                {"handler": JobUtils.Results.mediafile, "predefined": {"guid": "${mf1}", "source": {"url": "${src1}"}}}
            ]
        }
    })
    print(job.results[0].dumps())
    job_executor = JobExecutor()
    job_executor.run(job)
    working = True
    while working:
        # Listen to individual channel, timeout-blocking when finishing
        if job_executor.exec.error.is_set():
            Logger.critical('job {} failed\n'.format(job.guid))
            job_executor.exec.reset()
            break
        if job_executor.exec.finish.is_set():
            Logger.info('job {} finished\n'.format(job.guid))
            if job_executor.results():
                JobUtils.Results.process(job_executor.exec.job)
                # for r in job_executor.exec.job.results:
                #     Logger.warning('{}\n'.format(r.dumps()))
            break

        Logger.log('Job progress: {}\n'.format(job_executor.progress()))
        working = job_executor.working()
        time.sleep(1)

    job_executor.stop()
