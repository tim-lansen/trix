# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import os
import sys
import slugify
import hashlib
import codecs
import uuid
import time
import pprint
import traceback
from typing import List
from .log_console import Logger
from modules.config import TRIX_CONFIG
from modules.models import Fileset
from .job_utils import JobUtils
from modules.utils.database import DBInterface
from modules.utils.abs_paths import mount_paths


def process_file(root, fn, paths: dict):
    f_watch = os.path.join(root, fn)
    fe = fn.rsplit('.', 1)
    # Ignore files like '.pin'
    if len(fe[0]) == 0:
        return None
    if len(fe) != 2:
        Logger.error('File {} has no extension\n'.format(fn))
        f_failed = os.path.join(paths['fail'], fn)
        try:
            os.rename(f_watch, f_failed)
        except Exception as e:
            Logger.error('Failed to rename {} to {}\nError: {}\n'.format(f_watch, f_failed, e))
        return None
    fs = slugify.slugify(fn)
    while 1:
        # suffix = codecs.encode(hashlib.md5(uuid.uuid4()).digest(), 'hex')[:4].decode()
        suffix = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
        d_in_work = os.path.join(paths['work'], '{}_{}'.format(fs[:8], suffix))
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


def process_dir(root, dn, paths: dict):
    d_watch = os.path.join(root, dn)
    ds = slugify.slugify(dn)
    while 1:
        suffix = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
        d_in_work = os.path.join(paths['work'], '{}_{}'.format(ds[:8], suffix))
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
    for wf in TRIX_CONFIG.storage.watchfolders:
        paths = wf.accessible()
        if paths:
            for root, dirs, files in os.walk(paths['watch']):
                # Process individual files
                for fn in files:
                    res = process_file(root, fn, paths)
                    if res:
                        directories_in_work.append({'path': res, 'names': [fn]})
                # Process directories
                for dn in dirs:
                    res = process_dir(root, dn, paths)
                    if res:
                        directories_in_work.append({'path': res, 'names': [dn]})
                # Walk 1st level only
                break
    # process results
    for d in directories_in_work:
        job = JobUtils.CreateJob.ingest_prepare_sliced(d)
        Logger.info('Job created:\n{}\n'.format(job.dumps(indent=2)))
        # Create PROBE job
        # CreateJob.media_info(**d)


def update_filesets():
    filesets: List[Fileset] = []
    for wf in TRIX_CONFIG.storage.watchfolders:
        print(wf)
        paths = wf.accessible()
        if paths:
            filesets += Fileset.filesets(paths['watch'])
    fs_set = {_.name for _ in filesets}
    # Read name+guid of all filesets from DB
    fsdb = DBInterface.Fileset.records_fields({'guid', 'name'} | Fileset.FIELDS_FOR_UPDATE)
    tmp = [_['name'] for _ in fsdb]
    fsdb_map = {name: Fileset(fsdb[i]) for i, name in enumerate(tmp)}

    # Register new and update modified filesets
    for fs in filesets:
        if fs.name not in fsdb_map:
            fs.guid.new()
            fs.status = Fileset.Status.NEW
            DBInterface.Fileset.set(fs)
        elif fsdb_map[fs.name] != fs:
            Logger.error('{}\n{}\n'.format(fs, fsdb_map[fs.name]))
            DBInterface.Fileset.update_fields(fs, Fileset.FIELDS_FOR_UPDATE)
    # Remove absent filesets
    absent = [_ for _ in fsdb_map if _ not in fs_set]
    if len(absent):
        Logger.warning('Removing fileset(s):\n{}\n'.format('\n'.join(absent)))
        DBInterface.Fileset.remove_by_names(absent)


def test_update_filesets():
    mount_paths({'watch'})
    for i in range(50):
        update_filesets()
        time.sleep(5)

