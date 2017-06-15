# -*- coding: utf-8 -*-


import sys
import uuid
from modules.config import *
from modules.utils.log_console import Logger
from modules.utils.database import DBInterface
from modules.models import *


class Worker:

    def exit(self):
        Logger.warning('Exiting\n')
        DBInterface.Node.unregister(self.node, False)
        # TODO: stop running processes
        sys.exit(0)

    def ping(self):
        Logger.info('pong\n')
        DBInterface.Node.pong(self.node)
        # TODO: update status, job status/progress

    def offer(self):
        Logger.info('offer\n')

    def __init__(self, _name):
        self.node = Node()
        self.node.name = _name
        self.node.id = str(uuid.uuid4())
        self.node.channel = 'channel_{}'.format(self.node.id.replace('-', '_'))

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
                if n.payload in self.vectors:
                    self.vectors[n.payload](self)
                else:
                    Logger.warning("unknown command: {}\n".format(n.payload))


if __name__ == '__main__':
    # First argument is a name of node
    name = sys.argv[1]
    worker = Worker(name)
    worker.run()

