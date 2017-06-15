# -*- coding: utf-8 -*-


import sys
import uuid
# from modules.config import TRIX_CONFIG
from modules.utils import *
from modules.models import *


class Worker:

    def __init__(self, _name):
        self.node = Node()
        self.node.name = _name
        self.node.id = str(uuid.uuid4())
        self.node.channel = 'channel_{}'.format(self.node.id.replace('-', '_'))

    def handle_notification(self, message):
        if message == 'exit':
            Logger.info('Exiting\n')
            DBInterface.Node.unregister(self.node, False)
            DBInterface.Node.disconnect()
            # TODO: stop running processes
            sys.exit(0)
        elif message == 'ping':
            Logger.info('pong\n')
            # TODO: update mtime for node in DB

    def run(self):
        if not DBInterface.Node.register(self.node, False):
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
                self.handle_notification(n.payload)


if __name__ == '__main__':
    # First argument is a name of node
    name = sys.argv[1]
    worker = Worker(name)
    worker.run()

