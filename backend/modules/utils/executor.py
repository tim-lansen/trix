# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Chain execution

import os
import sys
import time
import json
import shutil
from typing import List
from multiprocessing import Process, Event
from modules.models.job import Job
from modules.utils.log_console import Logger
from .parsers import PARSERS
from .execute_chain import execute_chain
from .cross_process_lossy_queue import CPLQueue
from .resolve_job_aliases import resolve_job_aliases


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
        # while not self.force_exit.is_set():
        #     self.start.wait(timeout=1.0)
        #     if not self.start.is_set():
        #         continue
        #     self.start.clear()
        ex.running.set()
        # self._last_captured_progress = 0.0
        # flush_queue(self.job_progress_output)
        try:
            Logger.info("Starting job {}\n".format(ex.job.name))
            # Prepare paths
            for path in ex.job.info.paths:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                os.mkdir(path)
            for ai, step in enumerate(ex.job.info.steps):
                Logger.info("Step #{}\n".format(ai))
                # Prepare pipes
                for pipe in step.pipes:
                    os.mkfifo(pipe)
                step_queues = []
                monitors: List[Job.Info.Step.Chain] = []
                threads: List[Process] = []

                # Initialize and start step's chains execution, each chain in own thread
                for ci, chain in enumerate(step.chains):
                    # Workaround Python's bad threading
                    if len(threads):
                        time.sleep(1.0)
                    monitors.append(chain.progress)
                    # Multi-capture chain
                    queues = [CPLQueue(5)] * len(chain.procs)
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
                            if c and j == monitors[i].progress.capture:
                                if monitors[i].progress.parser in PARSERS:
                                    cap = PARSERS[monitors[i].progress.parser](c)
                                    if cap and 'pos' in cap:
                                        monitors[i].progress.done = cap['pos']
                                        # self.job.info.steps[ai].chains[i].progress.done =
                                        # info['steps'][ai]['progress'][i] = cap['pos']/monitors[i]['top']
                                        # # step_complete[ai][i] = cap['pos']/monitors[i]['top']
                    # calculate step progress
                    step_progress = 0.0
                    for m in monitors:
                        step_progress += m.progress.done/m.progress.top
                    job_progress = step_progress / (len(monitors) * len(ex.job.info.steps))
                    ex.progress_output.put('{{"step":{},"progress":{.3f}}}'.format(ai, job_progress))
                    time.sleep(0.5)

                # Step is finished, cleaning up
                for m in monitors:
                    m.progress.done = 1.0
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
            Logger.error("Job failed fff: {}\n".format(e))
            Logger.warning(ex.job.dumps())
            ex.error.set()
        ex.running.clear()
        # Set finish event only if no error
        if not ex.error.is_set():
            ex.finish.set()

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
