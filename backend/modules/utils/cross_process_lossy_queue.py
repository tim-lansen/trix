# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import multiprocessing
from .exchange import Exchange


class CPLQueue:
    def __init__(self, maxsize):
        self.q = multiprocessing.Queue()
        self.maxsize = maxsize

    def put(self, msg):
        # Lose least recent messages
        while self.q.qsize() >= self.maxsize:
            self.q.get()
        m = Exchange.object_encode(msg)
        self.q.put(m, timeout=2)

    def get(self, block=True, timeout=None):
        r = Exchange.object_decode(self.q.get(block=block, timeout=timeout))
        return r

    def flush(self):
        r = None
        while self.q.qsize() > 0:
            r = self.q.get()
        r = Exchange.object_decode(r)
        return r
