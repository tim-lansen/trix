# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import multiprocessing


class CPLQueue:
    def __init__(self, maxsize):
        # super().__init__()
        self.q = multiprocessing.Queue()
        self.maxsize = maxsize

    def put(self, msg):
        # Lose least recent messages
        while self.q.qsize() >= self.maxsize:
            self.q.get()
        self.q.put(msg, block=False)

    def flush(self):
        c1 = None
        while self.q.qsize() > 0:
            c1 = self.q.get()
        return c1
