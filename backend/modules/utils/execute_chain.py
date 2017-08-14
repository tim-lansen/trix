# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Chain execution

import os
import sys
import time
import json
import traceback
from typing import List

# from queue import Queue, Empty
# from threading import Thread, Event
from multiprocessing import Process, Event
from .cross_process_lossy_queue import CPLQueue

from subprocess import Popen, PIPE
from modules.models.job import Job
from modules.models.mediafile import MediaFile
from .log_console import Logger, tracer
from .combined_info import combined_info
from .commands import *
from .pipe_nowait import pipe_nowait
from .parsers import PARSERS
from .ffmpeg_utils import ffmpeg_create_preview_extract_audio_subtitles
from .storage import Storage


def internal_combined_info(params, out_progress: CPLQueue, out_final: CPLQueue):
    """
    Compose ffprobe and mediainfo
    :param params:            ['<predefined>', '<url>']
    :param out_progress:      progress output queue
    :param out_final:         final output queue
    :param chain_error_event: error event
    :return:
    """
    mf = MediaFile()
    mf.update_str(params[0])
    combined_info(mf, params[1])
    out_final.put(mf.dumps())


def internal_create_preview_extract_audio_subtitles(params, out_progress: CPLQueue, out_final: CPLQueue):
    """
    Prepare media for ingest
    :param params:            ['<predefined>', '<url>']
    :param out_progress:      progress output queue
    :param out_final:         final output queue
    :param chain_error_event: error event
    :return:
    """
    print(params)
    mf = MediaFile()
    mf.update_str(params[0])
    if mf.guid.is_null():
        mf.guid.new()
    combined_info(mf, params[1])
    tdir = Storage.storage_path('transit', str(mf.guid))
    pdir = Storage.storage_path('preview', str(mf.guid))
    res = ffmpeg_create_preview_extract_audio_subtitles(mf, tdir, pdir, out_progress)
    result = {
        'asset': res['asset'].dumps(),
        'trans': [_.dumps() for _ in res['trans']],
        'previews': [_.dumps() for _ in res['previews']],
        'archives': [_.dumps() for _ in res['archives']],
    }
    out_final.put(json.dumps(result))


def execute_internal(params: List[str],
                     out_progress: CPLQueue,
                     out_final: CPLQueue,
                     chain_error_event: Event):
    """
    Execute internal (complex) procedure, pass progress if able to, and pass final results
    :param params:            ['<procedure>', '<param1>', '<param2>', ...]
    :param out_progress:      progress output queue
    :param out_final:         final output queue
    :param chain_error_event: error event
    :return:
    """
    try:
        proc = globals()[params[0]]
        proc(params[1:], out_progress, out_final)
    except Exception as e:
        Logger.error('execute_internal failed: {}\n'.format(e))
        for frame in traceback.extract_tb(sys.exc_info()[2]):
            print(frame)
        chain_error_event.set()
    Logger.log('execute_internal finished\n')


# Execute chain object
# Chain description may be found in modules.models.job
# In short: Chain is a list of processes that being started simultaneously and compiled into a chain,
# where STDOUT of every process is attached to STDIN of next process
def execute_chain(chain: Job.Info.Step.Chain,
                  out_progress: List[CPLQueue],
                  out_result: CPLQueue,
                  chain_enter_event: Event,
                  chain_error_event: Event):
    chain_enter_event.set()
    if chain_error_event.is_set():
        Logger.error('Error event is already set\n')
        return
    # Handle special complex cases
    if len(chain.procs) == 1 and chain.procs[0][0].startswith('internal_'):
        execute_internal(chain.procs[0], out_progress[0], out_result, chain_error_event)
        return
    proc = []
    text = ['' for _ in chain.procs]
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
                        out_progress[i].put(line)
                except OSError as e:
                    pass
            else:
                # Check retcode
                rc = p.returncode
                if rc not in retcodes[i]:
                    # Error, stop chain
                    Logger.warning('Bad retcode in op#{0}: {1}\n'.format(i, rc))
                    chain_error_event.set()
                proc[i] = None
        time.sleep(0.4)
    Logger.log('Chain finished\n')
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
        r"ffmpeg -y -loglevel error -stats -i /mnt/server1_id/crude/in_work/test_eng1_20.mp4 -t 90 -map a:0 -c:a pcm_s32le -f sox -".split(' '),
        r"sox -t sox - -t sox - remix 1v0.5,2v0.5 sinc -p 10 -t 5 100-3500 -t 10".split(' '),
        r"ffmpeg -y -loglevel error -stats -f sox -i - -c:a aac -b:a 128k -strict -2 /mnt/server1_id/crude/in_work/test_eng1_20.chain.mp4".split(' ')
    ]
    test_chain.progress.capture = 2

    test_chain.progress.parser = 'ffmpeg'

    test_output: List[CPLQueue] = [CPLQueue(5) for _ in test_chain.procs]

    # Multi-capture chain
    test_process = Process(target=execute_chain, args=(test_chain, test_output, test_chain_enter, test_chain_error))
    test_process.start()

    test_chain_enter.wait()
    test_chain_enter.clear()

    def dummy_parser(c):
        Logger.warning('{}\n'.format(c))
        return None

    parser = dummy_parser if test_chain.progress.parser is None or test_chain.progress.parser not in PARSERS else PARSERS[test_chain.progress.parser]

    while True:
        if not test_process.is_alive():
            break
        # Compile info from chains
        for j, q in enumerate(test_output):
            c = q.flush('test')
            if c and j == test_chain.progress.capture:
                p = parser(c)
                Logger.log('{}\n'.format(p))
            time.sleep(0.1)

    Logger.critical('Done\n')

