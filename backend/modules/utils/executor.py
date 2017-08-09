# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Chain execution

import os
import sys
import time
import json
import uuid
import shutil
from typing import List
from multiprocessing import Process, Event
from modules.models.job import Job
from modules.utils.log_console import Logger
from .parsers import PARSERS
from .execute_chain import execute_chain
from .cross_process_lossy_queue import CPLQueue
from .resolve_job_aliases import resolve_job_aliases

from modules.models.mediafile import MediaFile
from .combined_info import combined_info


class JobExecutor:
    class Execution:

        def __init__(self):
            self.job: Job = None
            self.progress_output = CPLQueue(5)
            self.error = Event()
            self.finish = Event()
            self.running = Event()
            self.force_exit = Event()

        def reset(self):
            self.progress_output.flush()
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
                    step_queues.append(queues)
                    t = Process(target=execute_chain, args=(chain, queues, chain_enter, chain_error))
                    t.start()
                    threads.append(t)
                    chain_enter.wait()
                    chain_enter.clear()

                # Wait step to execute
                while True:
                    if not [t.is_alive() for t in threads].count(True):
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
                                    if cap and 'pos' in cap:
                                        monitors[i].done = cap['pos']
                    # calculate step progress
                    step_progress = 0.0
                    for m in monitors:
                        step_progress += m.done/m.top
                    job_progress = step_progress / (len(monitors) * len(ex.job.info.steps))
                    ex.progress_output.put('{{"step":{},"progress":{:.3f}}}'.format(ai, job_progress))
                    time.sleep(0.5)

                # Step is finished, cleaning up
                for m in monitors:
                    m.done = 1.0
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

    def results(self):
        if self.exec.job.info.results is None or len(self.exec.job.info.results) == 0:
            Logger.warning('No results to emit\n')
            return None
        res = []
        for result in self.exec.job.info.results:
            Logger.critical('{}\n'.format(result))

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
        self.exec.reset()
        resolve_job_aliases(job)
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
                                "parser": "ffmpeg",
                                "top": 600.0
                            }
                        }
                    ]
                }
            ],
            "results": [
                {'eval': ['mediafile = MediaFile()', ]},
                {"type": "MediaFile", "info": {"guid": "${new_media_id}", "source": {"url": "${f_dst}"}}}
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
