# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import os
import slugify
import hashlib
import codecs
import uuid
import time
from .log_console import Logger
from modules.config import TRIX_CONFIG
from .job_utils import CreateJob


def process_file(root, fn, path: TRIX_CONFIG.Storage.Server.Path):
    f_watch = os.path.join(root, fn)
    fe = fn.rsplit('.', 1)
    if len(fe) != 2:
        Logger.error('File {} has no extension\n'.format(fn))
        f_failed = os.path.join(path.failed, fn)
        try:
            os.rename(f_watch, f_failed)
        except Exception as e:
            Logger.error('Failed to rename {} to {}\nError: {}\n'.format(f_watch, f_failed, e))
        return None
    fs = slugify.slugify(fn)
    while 1:
        # suffix = codecs.encode(hashlib.md5(uuid.uuid4()).digest(), 'hex')[:4].decode()
        suffix = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
        d_in_work = os.path.join(path.in_work, '{}_{}'.format(fs[:8], suffix))
        new_filename = '{}_{}.{}'.format(fs[:8], suffix, fe[1].lower())
        if os.path.isdir(d_in_work) or os.path.isfile(d_in_work):
            time.sleep(1)
        else:
            break
    f_in_work = os.path.join(d_in_work, new_filename)
    try:
        os.mkdir(d_in_work)
        os.rename(f_watch, f_in_work)
    except Exception as e:
        Logger.error('Failed to rename {} to {}\nError: {}\n'.format(f_watch, f_in_work, e))
        return None
    return d_in_work


def process_dir(root, dn, path: TRIX_CONFIG.Storage.Server.Path):
    d_watch = os.path.join(root, dn)
    ds = slugify.slugify(dn)
    while 1:
        suffix = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
        d_in_work = os.path.join(path.in_work, '{}_{}'.format(ds[:8], suffix))
        if os.path.isdir(d_in_work) or os.path.isfile(d_in_work):
            time.sleep(1)
        else:
            break
    try:
        os.rename(d_watch, d_in_work)
    except Exception as e:
        Logger.error('Failed to rename {} to {}\nError: {}\n'.format(d_watch, d_in_work, e))
        return None
    return d_in_work


def watch_once():
    directories_in_work = []
    for s in TRIX_CONFIG.storage.servers:
        srv: TRIX_CONFIG.Storage.Server = s
        for p in srv.paths:
            path: srv.Path = p
            if path.role == path.Role.CRUDE:
                if path.watch is None or path.in_work is None or path.failed is None or path.path is None:
                    continue
                if os.path.isdir(path.watch) and os.path.isdir(path.in_work) and os.path.isdir(path.failed) and os.path.isdir(path.path):
                    for root, dirs, files in os.walk(path.watch):
                        # Process individual files
                        for fn in files:
                            res = process_file(root, fn, path)
                            if res:
                                directories_in_work.append({'path': res, 'names': [fn]})
                        # Process directories
                        for dn in dirs:
                            res = process_dir(root, dn, path)
                            if res:
                                directories_in_work.append({'path': res, 'names': [dn]})
                        # Walk 1st level only
                        break
    # process results
    for d in directories_in_work:
        print(d)
        # Create PROBE job
        CreateJob.media_info(**d)
