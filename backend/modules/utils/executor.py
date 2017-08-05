# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Chain execution

import os
import sys
import time
import json
import shutil
from typing import List
# from queue import Queue, Empty
# from threading import Thread, Event
from multiprocessing import Process, Queue, Event
from subprocess import Popen, PIPE
from modules.models.job import Job
from modules.utils.log_console import Logger
from .commands import *
from .pipe_nowait import pipe_nowait
from .parsers import PARSERS
from .execute_chain import execute_chain, flush_queue


class JobExecutor:
    def __init__(self):
        self.job_progress_output = Queue()
        self.job: Job = None
        self.start = Event()
        self.error = Event()
        self.finish = Event()
        self.process = Process(target=self._process)
        self.started = Event()
        # self._progress = 0.0
        self.force_exit = Event()
        self._last_captured_progress = 0.0

        self.process.start()

    def _process(self):
        chain_enter = Event()
        chain_error = Event()
        while not self.force_exit.is_set():
            self.start.wait(timeout=1.0)
            if not self.start.is_set():
                continue
            self.start.clear()
            self._last_captured_progress = 0.0
            flush_queue(self.job_progress_output)
            Logger.info("Starting job {}\n".format(self.job.name))
            # Prepare
            for path in self.job.info.paths:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                os.mkdir(path)
            for ai, step in enumerate(self.job.info.steps):
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
                    queues = [Queue()] * len(chain.procs)
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
                            c = flush_queue(q)
                            if c and j == monitors[i].progress.capture:
                                if monitors[i].progress.parser in PARSERS:
                                    cap = PARSERS[monitors[i].progress.parser](c)
                                    if cap and 'pos' in cap:
                                        monitors[i].progress.done = cap['pos']
                                        # self.job.info.steps[ai].chains[i].progress.done =
                                        # info['steps'][ai]['progress'][i] = cap['pos']/monitors[i]['top']
                                        # # step_complete[ai][i] = cap['pos']/monitors[i]['top']
                    # calc step progress
                    step_progress = 0.0
                    for m in monitors:
                        step_progress += m.progress.done/m.progress.top
                    job_progress = step_progress / (len(monitors) * len(self.job.info.steps))
                    self.job_progress_output.put('{{"step":{},"progress":{.3f}}}'.format(ai, job_progress), timeout=5.0)
                    time.sleep(0.5)

                for m in monitors:
                    m.progress.done = 1.0
                for pipe in step.pipes:
                    os.remove(pipe)
                if chain_error.is_set():
                    chain_error.clear()
                    Logger.error("Job failed on step {}\n".format(ai))
                    self.error.set()
                    break
                Logger.info("Step {} finished\n".format(ai))
                self.job_progress_output.put('{{"step":{},"progress":{:.3f}}}'.format(ai, (ai + 1.0)/len(self.job.info.steps)))
            Logger.info("Job finished\n")
            self.finish.set()

    def progress(self):
        cap = flush_queue(self.job_progress_output)
        if cap is not None:
            jcap = json.loads(cap)
            self._last_captured_progress = jcap['progress']
        return self._last_captured_progress

    def run(self, job: Job):
        if self.process is not None:
            Logger.error("ExecuteStep.run: busy\n")
            return False
        self.job = job
        self.error.clear()
        self.finish.clear()
        self.started.clear()
        self.start.set()
        self.started.wait(timeout=10.0)
        if self.started.is_set():
            Logger.info("Job execution started\n")
            return True
        Logger.error("Failed to start job execution\n")
        if not self.process.is_alive():
            Logger.warning("Thread is dead, starting it\n")
            self.process = Process(self._process)
        return False

    def stop(self):
        self.force_exit.set()
        self.process.join(timeout=5)
