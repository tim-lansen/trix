# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import multiprocessing
import base64
import pickle
from .log_console import Logger


class CPLQueue:
    def __init__(self, maxsize):
        self.q = multiprocessing.Queue()
        self.maxsize = maxsize

    def put(self, msg):
        # Lose least recent messages
        while self.q.qsize() >= self.maxsize:
            self.q.get()
        m = base64.b64encode(pickle.dumps(msg))
        self.q.put(m, timeout=2)

    def get(self, block=True, timeout=None):
        r = self.q.get(block=block, timeout=timeout)
        if r:
            r = pickle.loads(base64.b64decode(r))
        return r

    def flush(self):
        r = None
        while self.q.qsize() > 0:
            r = self.q.get()
        if r:
            r = pickle.loads(base64.b64decode(r))
        return r
