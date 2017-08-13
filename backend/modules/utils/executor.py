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
import shutil
from copy import deepcopy
from typing import List
from multiprocessing import Process, Event
from modules.models.job import Job
from modules.models.interaction import Interaction
from modules.utils.log_console import Logger, tracer
from .parsers import PARSERS, timecode_to_float
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
            self.error = Event()
            self.finish = Event()
            self.running = Event()
            self.force_exit = Event()

        def reset(self, finals_count=0):
            self.progress_output.flush()
            for f in self.finals:
                f.flush()
            if len(self.finals) < finals_count:
                self.finals += [CPLQueue(2) for _ in range(finals_count - len(self.finals))]
            # self.final.flush()
            self.error.clear()
            self.finish.clear()
            self.running.clear()
            self.force_exit.clear()

    def __init__(self):
        self.exec = JobExecutor.Execution()
        self.process: Process = None
        self._last_captured_progress = 0.0

    @staticmethod
    def _process(ex: Execution):
        chain_enter = Event()
        chain_error = Event()
        ex.running.set()
        try:
            Logger.info("Starting job {}\n".format(ex.job.name))
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
                step_queues = []
                monitors: List[Job.Info.Step.Chain.Progress] = []
                threads: List[Process] = []

                # Initialize and start step's chains execution, each chain in own thread
                for ci, chain in enumerate(step.chains):
                    # Workaround Python's bad threading
                    if len(threads):
                        time.sleep(1.0)
                    monitors.append(chain.progress)
                    # Multi-capture chain
                    queues = [CPLQueue(5) for _ in chain.procs]
                    qfinal = None if chain.result is None else ex.finals[ci]
                    step_queues.append(queues)
                    t = Process(target=execute_chain, args=(chain, queues, qfinal, chain_enter, chain_error))
                    t.start()
                    threads.append(t)
                    chain_enter.wait()
                    chain_enter.clear()

                # Wait step to execute
                while True:
                    if [t.is_alive() for t in threads].count(True) == 0:
                        break
                    # Compile info from chains
                    for i, que in enumerate(step_queues):
                        # Multi-chain capture
                        for j, q in enumerate(que):
                            c = q.flush()
                            if c is None:
                                continue
                            if j == monitors[i].capture:
                                if monitors[i].parser in PARSERS:
                                    cap = PARSERS[monitors[i].parser](c)
                                    if cap:
                                        if 'time' in cap:
                                            monitors[i].pos = timecode_to_float(cap['time'])
                                        elif 'progress' in cap:
                                            # Variant when chain executor sends progress rather than time, and m.top is set to 1.0
                                            monitors[i].pos = cap['progress']
                    # calculate step progress
                    step_progress = 0.0
                    for m in monitors:
                        step_progress += m.pos/m.top
                    job_progress = step_progress / (len(monitors) * len(ex.job.info.steps))
                    ex.progress_output.put('{{"step":{},"progress":{:.3f}}}'.format(ai, job_progress))
                    time.sleep(0.5)

                # Step is finished, cleaning up
                for m in monitors:
                    m.pos = 1.0
                for pipe in step.pipes:
                    os.remove(pipe)
                if chain_error.is_set():
                    chain_error.clear()
                    Logger.error("Job failed on step {}\n".format(ai))
                    ex.error.set()
                    break
                Logger.info("Step {} finished\n".format(ai))
                ex.progress_output.put('{{"step":{},"progress":{:.3f}}}'.format(ai, (ai + 1.0)/len(ex.job.info.steps)))
            Logger.info("Job finished\n")
        except Exception as e:
            Logger.error("Job failed: {}\n".format(e))
            Logger.traceback()
            Logger.warning('{}\n'.format(ex.job.dumps()))
            ex.error.set()
        ex.running.clear()
        # Set finish event only if no error
        if not ex.error.is_set():
            ex.finish.set()

    def _result_(self, r: Job.Info.Result):
        pass

    def _result_interaction(self, r: Job.Info.Result):
        # Create an interaction and push it to DB
        inter = Interaction()
        inter.update_json(r.predefined)
        r.actual = MediaFile()
        # combined_info(r.actual, r.path)

    def _result_mediafile(self, r: Job.Info.Result):
        r.actual = MediaFile()
        r.actual.update_str(self.exec.finals[r.index].get(timeout=1))

    def _result_combined_info(self, r: Job.Info.Result):
        r.actual = MediaFile()
        r.actual.update_str(self.exec.finals[r.index].get(timeout=1))

    VECTORS = {
        Job.Info.Result.Type.INTERACTION: _result_interaction,
        Job.Info.Result.Type.MEDIAFILE: _result_mediafile,
        Job.Info.Result.Type.ASSET: _result_,
        # Job.Info.Result.Type.COMBINED_INFO: _result_combined_info,
        Job.Info.Result.Type.FILE: _result_,
        Job.Info.Result.Type.TASK: _result_,
        Job.Info.Result.Type.JOB: _result_
    }

    def results(self):
        if self.exec.job.info.results is None:
            Logger.warning('No results to emit\n')
            return None
        rcount = 0
        for result in self.exec.job.info.results:
            # Logger.critical('{}\n'.format(result))
            result.index = rcount
            if result.type in JobExecutor.VECTORS:
                JobExecutor.VECTORS[result.type](self, result)
            rcount += 1
        return rcount

    def working(self):
        return self.process and self.process.is_alive()

    def progress(self):
        cap = self.exec.progress_output.flush()
        if cap is not None:
            jcap = json.loads(cap)
            self._last_captured_progress = jcap['progress']
        return self._last_captured_progress

    def run(self, job: Job):
        if self.process:
            if self.process.is_alive():
                Logger.error("JobExecutor.run: process is alive!\n")
                return False
            self.process = None
        self._last_captured_progress = 0.0
        self.exec.reset(job.info.max_parallel_chains())
        JobUtils.resolve_aliases(job)
        self.exec.job = job
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
                {"type": Job.Result.Type.MEDIAFILE, "info": {"guid": "${new_media_id}", "source": {"url": "${f_dst}"}}}
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
                {"type": Job.Info.Result.Type.MEDIAFILE, "predefined": {"guid": "${mf0}", "source": {"url": "${src0}"}}},
                {"type": Job.Info.Result.Type.MEDIAFILE, "predefined": {"guid": "${mf1}", "source": {"url": "${src1}"}}}
            ]
        }
    })
    print(job.info.results[0].dumps())
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
                JobUtils.RESULTS.process(job_executor.exec.job.info.results)
                # for r in job_executor.exec.job.info.results:
                #     Logger.warning('{}\n'.format(r.dumps()))
            break

        Logger.log('Job progress: {}\n'.format(job_executor.progress()))
        working = job_executor.working()
        time.sleep(1)

    job_executor.stop()
