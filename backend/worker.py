# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Worker node
# Run 'python worker.py' on target computer
# The worker will use it's IP address as part of name: "<IP address>#<index>"
# The worker will first try to get from DB list of
# Interface: DB channel for offering a complex job or immediate execution


import os
import sys
import uuid
import time
import shutil
import modules.utils.worker_mount_paths
from modules.utils.non_daemonic_pool import NonDaemonicPool
from modules.config import *
from modules.utils.log_console import Logger, tracer
from modules.utils.database import DBInterface
from modules.utils.executor import JobExecutor
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

    @tracer
    def exit(self, params):
        Logger.warning('Exiting ({})\n'.format(self.node.name))
        DBInterface.Node.unregister(self.node, False)
        # TODO: stop running processes
        self.job_executor.stop()
        # self.working = False
        self.node.status = Node.Status.EXITING

    @tracer
    def finish(self, params):
        Logger.warning('Finishing ({})\n'.format(self.node.name))
        # self.working = False
        self.node.status = Node.Status.FINISHING

    @tracer
    def ping(self, params):
        Logger.info('pong\n')
        DBInterface.Node.pong(self.node)
        # TODO: update status, job status/progress
        if self.node.status == Node.Status.BUSY:
            progress = self.job_executor.progress()
            DBInterface.Job.set_fields(self.job.guid, {'progress': progress})

    def _revert_(self, msg, revert_job=True):
        Logger.error(msg)
        if revert_job:
            # Try to revert job status
            if not DBInterface.Job.set_status(self.node.job, Job.Status.OFFERED):
                Logger.error("Failed to revert job status {}\n".format(self.node.job))
        # Try to revert node status
        if not DBInterface.Node.set_status(self.node.guid, Node.Status.IDLE):
            Logger.critical("Failed to revert node status {}\n".format(self.node.job))
            self.exit('failed to revert node status')
        self.node.status = Node.Status.IDLE

    def offer(self, params):
        Logger.info('Offered job: {}\n'.format(params[1]))
        if self.node.status != Node.Status.IDLE:
            Logger.error("Worker is busy\n")
            return

        self.node.job = params[1]
        # Set node status to BUSY
        if not DBInterface.Node.set_status(self.node.guid, Node.Status.BUSY):
            Logger.error("Failed to get BUSY\n")
            return
        self.node.status = Node.Status.BUSY

        # Change job status
        if not DBInterface.Job.set_status(self.node.job, Job.Status.EXECUTING):
            self._revert_("Failed change job status\n", False)
            return

        # Get job
        self.job = DBInterface.Job.get(self.node.job)
        if self.job is None:
            self._revert_("Failed to get job {}\n".format(self.node.job))
            return

        # Start execution
        if not self.job_executor.run(self.job):
            self._revert_("Failed to start job execution {}\n".format(self.node.job))

    @tracer
    def __init__(self, _name, _channel):
        self.node = Node()
        self.node.name = _name
        self.node.channel = _channel
        self.node.guid = str(uuid.uuid4())
        # self.node.channel = 'channel_{}'.format(self.node.guid.replace('-', '_'))
        self.job: Job = None
        self.job_executor = JobExecutor()
        # self.working = False

    Vectors = {
        'exit': exit,
        'finish': finish,
        'ping': ping,
        'offer': offer
    }

    @tracer
    def run(self):
        if not DBInterface.Node.register(self.node):
            Logger.warning('Failed to register the node {}\n'.format(self.node.name))
            return
        Logger.info("Registered self as '{}' ({})\n".format(self.node.name, self.node.guid))
        # Starting loop
        invalid_status_set = {
            Node.Status.EXITING,
            Node.Status.FINISHING,
            Node.Status.INVALID
        }
        working = True
        while working or self.job:
            # Listen to individual channel, timeout-blocking when finishing
            notifications = DBInterface.Node.listen(self.node, blocking=working)
            if notifications is None:
                Logger.warning('Listening failed\n')
                break
            for n in notifications:
                Logger.info("Got NOTIFY: {} {} {}\n".format(n.pid, n.channel, n.payload))
                params = n.payload.split(' ')
                if params[0] in Worker.Vectors:
                    Worker.Vectors[params[0]](self, params)
                else:
                    Logger.warning("unknown command: {}\n".format(n.payload))
            Logger.info('Node: {}\n'.format(self.node.dumps()))
            working = self.node.status not in invalid_status_set

        DBInterface.Node.unregister(self.node, False)


def launch_node(name, channel, job_types):
    worker = Worker(name, channel)
    worker.run()
    return name


def run_worker():
    # if len(sys.argv) == 1:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((TRIX_CONFIG.dBase.connection.host, 1))
    ip_address = s.getsockname()[0]
    mach = DBInterface.Machine.get_by_ip(ip_address)
    if mach is None:
        # No machine with this IP is registered in DB, get setup from config and register
        if ip_address in TRIX_CONFIG.machines.unmentioned:
            tmpl = TRIX_CONFIG.machines.unmentioned[ip_address]
        else:
            tmpl = TRIX_CONFIG.machines.default
        mach = Machine()
        mach.guid.new()
        mach.update_json(tmpl)
        # superhack
        if os.name == 'nt' and mach.tmp.startswith('/'):
            mach.tmp = 'C:\\' + mach.tmp[1:].replace('/', '\\')
        mach.hardware.cpu = get_cpu_info()
        if mach.name is None:
            mach.name = 'Machine {}'.format(ip_address)
        mach.ip = ip_address
        DBInterface.Machine.register(mach)

    ars = []
    for ni, nj in enumerate(mach.node_job_types):
        name = '{}_{}'.format(ip_address, ni)
        channel = 'ch_{}'.format(name.replace('.', '_'))
        tmp = os.path.join(mach.tmp, 'trix_{:02d}'.format(ni))
        if not dir_clear_create(tmp):
            Logger.critical('Worker {}: failed to create directory {}\n'.format(ip_address, tmp))
            exit(1)
        ars.append([name, channel, nj])
    # Starting child node with params
    # with NonDaemonicPool(processes=len(mach.node_job_types)) as pool:
    #     # for ni, nj in enumerate(mach.node_job_types):
    #     for a in ars:
    #         # name = '{}_{}'.format(ip_address, ni)
    #         # channel = 'ch_{}'.format(name.replace('.', '_'))
    #         # params = {'name': name, 'job_types': nj}
    #         r = pool.apply_async(launch_node, args=tuple(a), callback=lambda x: print('FINISHED:', x), error_callback=lambda e: print('ERROR!', e))
    #         a.append(r)
    #
    #     falling = False
    #     while 1:
    #         ready = [_[3].ready() for _ in ars]
    #         finished_count = ready.count(True)
    #         if finished_count > 0:
    #             if finished_count == len(ars):
    #                 break
    #             if not falling:
    #                 falling = True
    #                 # Send notifications (only once)
    #                 notes = [[ars[_][1], 'finish'] for _ in range(len(ars)) if not ready[_]]
    #                 DBInterface.notify_list(notes)
    #         time.sleep(4)

    Logger.critical('Worker {} is done\n'.format(ip_address))


if __name__ == '__main__':
    if len(sys.argv) == 3:
        launch_node(sys.argv[1], sys.argv[2], None)
    else:
        if modules.utils.worker_mount_paths.mount_paths():
            run_worker()
