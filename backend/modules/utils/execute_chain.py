# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Chain execution

import os
import sys
import time
from typing import List

# from queue import Queue, Empty
# from threading import Thread, Event
from multiprocessing import Queue, Process, Event

from subprocess import Popen, PIPE
from modules.models.job import Job
from modules.utils.log_console import Logger
from .commands import *
from .pipe_nowait import pipe_nowait
from .parsers import PARSERS


# Read all queued objects, return last
def flush_queue(que: Queue):
    c1 = None
    while True:
        c2 = c1
        try:
            c1 = que.get_nowait()
        except:
            break
    return c2


# Execute chain object
# Chain description may be found in modules.models.job
# In short: Chain is a list of processes that being started simultaneously and compiled into a chain,
# where STDOUT of every process is attached to STDIN of next process
def execute_chain(chain: Job.Info.Step.Chain, output: List[Queue], chain_enter_event: Event, chain_error_event: Event):
    chain_enter_event.set()
    if chain_error_event.is_set():
        Logger.error('Error event is already set\n')
        return
    proc = []
    text = [''] * len(chain.procs)
    stderr_nbsr = []
    pstdout = PIPE
    Logger.info('{0}\n'.format(' \\\n|'.join([format_command(_) for _ in chain.procs])))
    for i, c in enumerate(chain.procs):
        try:
            p = Popen(c, stdin=pstdout, stdout=PIPE, stderr=PIPE)
        except Exception as e:
            Logger.error('Failed to launch {0}\n'.format(c[0]))
            Logger.error('{0}\n'.format(e))
            # Stop procs that already launched
            while i > 0:
                i -= 1
                Logger.warning('Stopping proc #{0}\n'.format(i))
                proc[i].kill()
                proc[i].wait()
            chain_error_event.set()
            return
        pipe_nowait(p.stderr)
        proc.append(p)
        pstdout = p.stdout
        stderr_nbsr.append(p.stderr.fileno())
        # stderr_nbsr.append(p.stderr)
    for p in proc:
        p.stdout.close()
    all_completed = False
    retcodes = chain.return_codes
    print(retcodes)
    while not all_completed:
        all_completed = True
        if chain_error_event.is_set():
            for i, p in enumerate(proc):
                if p is not None:
                    Logger.warning('Stopping proc #{0}\n'.format(i))
                    p.kill()
                    p.wait()
                proc[i] = None
            break
        for i, p in enumerate(proc):
            # Skip finished process
            if p is None:
                continue
            if p.poll() is None:
                all_completed = False
                s = stderr_nbsr[i]
                try:
                    part = os.read(s, 65536).decode().replace('\r', '\n').replace('\n\n', '\n')
                    text[i] += part
                    line = part.strip().rsplit('\n', 1)[-1]
                    if len(line):
                        output[i].put(line)
                except OSError as e:
                    pass
            else:
                # Check retcode
                rc = p.returncode
                # utils.write_console_colored('Return Code of #{0} is {1}\n'.format(i, rc), color=3)
                if str(i) in retcodes and rc not in retcodes[str(i)]:
                    # Error, stop chain
                    Logger.warning('Bad retcode in op#{0}: {1}\n'.format(i, rc))
                    chain_error_event.set()
                proc[i] = None
        time.sleep(0.4)
    Logger.info('Chain finished\n')
    # for i, t in enumerate(text):
    #     sys.stderr.write('\x1b[0;1;{0}m{1}\n\x1b[0m'.format(29 + i, t))
    # print('Execute chain finished')


def test():
    test_chain_enter = Event()
    test_chain_error = Event()

    test_chain = Job.Info.Step.Chain()
    test_chain.return_codes = [[0], [0]]

    # test_chain.procs = [
    #     "ffmpeg -y -loglevel error -stats -i F:\Kinozal\Der.gezaehmte.Widerspenstige.1980.720p.BluRay.mkv -t 60 -map v:0 -c:v libx264 -b:v 1000k -preset slow -g 50 -refs 2 -f mp4 nul".split(' ')
    # ]
    # test_chain.progress.capture = 0
    test_chain.procs = [
        r"ffmpeg -y -loglevel error -stats -i F:\Kinozal\Der.gezaehmte.Widerspenstige.1980.720p.BluRay.mkv -t 90 -map a:0 -c:a pcm_s32le -f sox -".split(' '),
        r"sox -t sox - -t sox - remix 1v0.5,2v-0.5 sinc -p 10 -t 5 100-3500 -t 10".split(' '),
        r"ffmpeg -y -loglevel error -stats -f sox -i - -c:a aac -b:a 128k -strict -2 C:\temp\test_chain_audio.mp4".split(' ')
    ]
    test_chain.progress.capture = 2

    test_chain.progress.parser = 'ffmpeg'

    test_output: List[Queue] = [Queue()] * len(test_chain.procs)

    # que = multiprocessing.Queue()
    # que.get_nowait()

    # Multi-capture chain
    test_process = Process(target=execute_chain, args=(test_chain, test_output, test_chain_enter, test_chain_error))
    time.sleep(1.0)
    test_process.start()

    test_chain_enter.wait()
    test_chain_enter.clear()

    def dummy_parser(c):
        return None

    parser = dummy_parser if test_chain.progress.parser is None or test_chain.progress.parser not in PARSERS else \
    PARSERS[test_chain.progress.parser]

    while True:
        if not test_process.is_alive():
            break
        # Compile info from chains
        for j, q in enumerate(test_output):
            c = flush_queue(q)
            if c and j == test_chain.progress.capture:
                p = parser(c)
                Logger.log('{}\n'.format(p))
            time.sleep(0.1)


