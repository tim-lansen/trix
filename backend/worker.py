# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Worker node
# Interface: DB channel for offering a complex job or immediate execution


import os
import sys
import uuid
import time
import shutil
import platform
from multiprocessing import Process, Event, Queue
import modules.utils.mount_paths
# from modules.utils.non_daemonic_pool import NonDaemonicPool
# from typing import List
from modules.config import *
from modules.utils.log_console import Logger, tracer
from modules.utils.database import DBInterface
from modules.utils.executor import JobExecutor
from modules.utils.node_utils import node_abilities, node_abilities_to_set
from modules.utils.cpuinfo import get_cpu_info
from modules.models import *


def dir_clear_create(path):
    result = True
    if os.path.isfile(path):
        os.remove(path)
        time.sleep(1)
    if os.path.isdir(path):
        for f in os.listdir(path):
            fp = os.path.join(path, f)
            try:
                shutil.rmtree(fp)
            except OSError:
                os.remove(fp)
    else:
        try:
            os.mkdir(path)
        except OSError:
            result = False
    return result


class Worker:

    def exit(self, params):
        """
        Force node to stop processing and exit
        :param params: don't care
        :return:
        """
        Logger.debug('Exiting ({})\n'.format(self.node.name), Logger.LogLevel.LOG_WARNING)

        # TODO: stop running processes
        if self.job_executor.exec.running.is_set():
            self.job_executor.stop()
            DBInterface.Job.set_status(self.node.job, Job.Status.CANCELED)
        self.node.status = Node.Status.EXITING
        DBInterface.Node.remove(self.node, False)
        # self.node.job = None

    def finish(self, params):
        Logger.debug('Finishing ({})\n'.format(self.node.name), Logger.LogLevel.LOG_WARNING)
        self.node.status = Node.Status.FINISHING

    def ping(self, params):
        Logger.debug('pong\n', Logger.LogLevel.LOG_INFO)
        DBInterface.Node.pong(self.node)
        # TODO: update status, job status/progress
        if self.node.status == Node.Status.BUSY:
            progress = self.job_executor.progress()
            DBInterface.Job.set_fields(self.node.job, {'progress': progress})

    def _revert_(self, msg, revert_job=True):
        Logger.debug(msg, Logger.LogLevel.LOG_ERR)
        if revert_job:
            # Try to revert job status
            if not DBInterface.Job.set_status(self.node.job, Job.Status.OFFERED):
                Logger.error("Failed to revert job status {}\n".format(self.node.job))
        # Try to revert node status
        if not DBInterface.Node.set_status(self.node.guid, Node.Status.IDLE):
            Logger.critical("Failed to revert node status {}\n".format(self.node.name))
            self.exit('failed to revert node status')
        self.node.status = Node.Status.IDLE

    def offer(self, params):
        Logger.debug('Offered job: {}\n'.format(params[1]), Logger.LogLevel.LOG_INFO)
        if self.node.status != Node.Status.IDLE:
            Logger.debug("Worker is busy\n", Logger.LogLevel.LOG_WARNING)
            return

        self.node.job = params[1]
        # Set node status to BUSY
        # if not DBInterface.Node.set_status(self.node.guid, Node.Status.BUSY):
        #     Logger.error("Failed to get BUSY\n")
        #     return
        if not DBInterface.Node.set_fields(self.node.guid, {'status': Node.Status.BUSY, 'job': "'{}'".format(self.node.job)}):
            Logger.debug("Failed to get BUSY\n", Logger.LogLevel.LOG_ERR)
            return
        self.node.status = Node.Status.BUSY

        # Change job status
        if not DBInterface.Job.set_status(self.node.job, Job.Status.EXECUTING):
            self._revert_("Failed change job status\n", False)
            return

        # Get job
        job = DBInterface.Job.get(self.node.job)
        if job is None:
            self._revert_("Failed to get job {}\n".format(self.node.job))
            return

        # Start execution
        if not self.job_executor.run(job):
            self._revert_("Failed to start job execution {}\n".format(self.node.job))

    def __init__(self, name, channel, abilities_mask):
        self.node = Node()
        self.node.name = name
        self.node.channel = channel
        self.node.guid = str(uuid.uuid4())
        self.node.roleMask = abilities_mask
        self.job_executor: JobExecutor = JobExecutor()

    Vectors = {
        'exit': exit,
        'finish': finish,
        'ping': ping,
        'offer': offer
    }

    def run(self):
        if not DBInterface.Node.register(self.node):
            Logger.warning('Failed to register the node {}\n'.format(self.node.name))
            self.job_executor.stop()
            return
        Logger.debug("Registered self as '{}' ({})\n".format(self.node.name, self.node.guid), Logger.LogLevel.LOG_INFO)
        # Starting loop
        invalid_status_set = {
            Node.Status.EXITING,
            Node.Status.FINISHING,
            Node.Status.INVALID
        }
        valid_status_set = {
            Node.Status.IDLE,
            Node.Status.BUSY
        }
        working = True
        while working:
            # Listen to individual channel, timeout-blocking when finishing
            notifications = DBInterface.Node.listen(self.node, blocking=False)
            if notifications is None:
                Logger.warning('Listening failed\n')
                break
            for n in notifications:
                Logger.debug("Got Notify: {} {} {}\n".format(n.pid, n.channel, n.payload), Logger.LogLevel.LOG_NOTICE)
                params = n.payload.split(' ')
                if params[0] in Worker.Vectors:
                    Worker.Vectors[params[0]](self, params)
                else:
                    Logger.warning("unknown command: {}\n".format(n.payload))

            if self.job_executor.exec.error.is_set():
                Logger.error('job {} failed\n'.format(self.node.job), Logger.LogLevel.LOG_CRIT)
                DBInterface.Job.set_status(self.node.job, Job.Status.FAILED)
                self.node.job = None
                if self.node.status == Node.Status.BUSY:
                    self.node.status = Node.Status.IDLE
                self.job_executor.exec.reset()
            if self.job_executor.exec.finish.is_set():
                # Default job status after execution is 'FINISHED'
                job_status = Job.Status.FINISHED
                r = self.job_executor.results()
                if r is not None:
                    if r == 0:
                        # Job considered FAILED if result is False
                        job_status = Job.Status.FAILED
                    # else:
                    #    Logger
                DBInterface.Job.set_status(self.node.job, job_status)
                self.node.job = None
                if self.node.status == Node.Status.BUSY:
                    self.node.status = Node.Status.IDLE
                self.job_executor.exec.reset()

            Logger.debug('Node: {}\n'.format(self.node.dumps()), Logger.LogLevel.LOG_INFO)
            working = self.node.status in valid_status_set or self.job_executor.working()

        DBInterface.Node.remove(self.node, False)


def launch_node(node_index, abilities):
    Logger.set_console_level(Logger.LogLevel.LOG_NOTICE)
    name = '{}_{:02d}'.format(platform.node().replace('-', '_'), node_index)
    channel = '{}_ch'.format(name)
    worker = Worker(name, channel, abilities)
    worker.run()
    return node_index


def run_worker(limit_node_count=16):
    if not modules.utils.mount_paths.abs_paths():
        Logger.critical('Failed to mount all necessary paths\n')
        exit(1)
    abilities = node_abilities()
    processes = []
    Logger.debug('Machine abilities:\n{}\n'.format('\n'.join(sorted(list(node_abilities_to_set(abilities))))))
    for idx, am in enumerate(TRIX_CONFIG.nodes.roles):
        if limit_node_count < 1:
            break
        limit_node_count -= 1
        mask = abilities & am
        if mask != 0:
            with open(os.devnull, 'w') as nul:
                proc = Process(target=launch_node, name='trix-worker-node#{:02d}'.format(idx), args=(idx, mask))
                proc.start()
                processes.append(proc)
        else:
            Logger.debug('Node {} has no suggested abilities:\n{}\n'.format(
                idx,
                node_abilities_to_set(am)
            ), Logger.LogLevel.LOG_ERR)
    # Start monitoring
    if len(processes):
        Logger.debug('Machine monitor started\n')
        while 1:
            if [_.is_alive() for _ in processes].count(True) == 0:
                break
            time.sleep(3)
        Logger.debug('All processes are down\n')
    else:
        Logger.debug('No processes to start\n')


if __name__ == '__main__':
    # Logger.set_level(Logger.LogLevel.LOG_NOTICE)
    try:
        run_worker(int(sys.argv[1]))
    except:
        run_worker()
