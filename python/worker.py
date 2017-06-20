# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Worker node
# Run 'python worker.py <node name>' on target computer
# Interface: DB channel for offering a complex job or immediate execution


import sys
import uuid
from modules.config import *
from modules.utils.log_console import Logger
from modules.utils.database import DBInterface
from modules.utils.executor import JobExecutor
from modules.models import *


class Worker:

    def exit(self, params):
        Logger.warning('Exiting ({})\n'.format(params))
        DBInterface.Node.unregister(self.node, False)
        # TODO: stop running processes
        self.job_executor.stop()
        sys.exit(0)

    def ping(self, params):
        Logger.info('pong\n')
        DBInterface.Node.pong(self.node)
        # TODO: update status, job status/progress
        if self.node.status == Node.Status.BUSY:
            progress = self.job_executor.progress()
            DBInterface.Job.set_fields(self.job.id, {'progress': progress})

    def _revert_(self, msg, revert_job=True):
        Logger.error(msg)
        if revert_job:
            # Try to revert job status
            if not DBInterface.Job.set_status(self.node.job, Job.Status.OFFERED):
                Logger.error("Failed to revert job status {}\n".format(self.node.job))
        # Try to revert node status
        if not DBInterface.Node.set_status(self.node.id, Node.Status.IDLE):
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
        if not DBInterface.Node.set_status(self.node.id, Node.Status.BUSY):
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

    def __init__(self, _name):
        self.node = Node()
        self.node.name = _name
        self.node.id = str(uuid.uuid4())
        self.node.channel = 'channel_{}'.format(self.node.id.replace('-', '_'))

        # TODO: set self.node.hardware
        self.node.hardware.cpu = 'i7 2700k'

        self.job: Job = None
        self.job_executor = JobExecutor()

        self.vectors = {
            'exit': Worker.exit,
            'ping': Worker.ping,
            'offer': Worker.offer
        }

    def run(self):
        if not DBInterface.Node.register(self.node):
            Logger.warning('Failed to register the node {}\n'.format(self.node.name))
            sys.exit(1)
        Logger.info("Registered self as '{}' ({})\n".format(self.node.name, self.node.id))
        # Starting loop
        while 1:
            # Listen to individual channel
            notifications = DBInterface.Node.listen(self.node)
            if notifications is None:
                Logger.warning('Listening failed\n')
                break
            for n in notifications:
                Logger.info("Got NOTIFY: {} {} {}\n".format(n.pid, n.channel, n.payload))
                params = n.payload.split(' ')
                if params[0] in self.vectors:
                    self.vectors[params[0]](self, params)
                else:
                    Logger.warning("unknown command: {}\n".format(n.payload))


if __name__ == '__main__':
    # First argument is a name of node
    name = sys.argv[1]
    worker = Worker(name)
    worker.run()

