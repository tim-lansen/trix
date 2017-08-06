# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import re
import os
import json
from typing import List
from modules.models.job import Job
from modules.utils.database import DBInterface
from .log_console import Logger


class CreateJob:

    @staticmethod
    def media_info(path, names: List[str]):
        """
        Create a job that analyzes source(s) and creates MediaFile(s)
        :param path: path to file or directory
        :param names: strings that may help to identify media
        :return: job GUID or None
        """
        paths = []
        if os.path.isfile(path):
            paths.append(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    paths.append(os.path.join(root, f))
        if len(paths) == 0:
            Logger.error('Cannot find file(s) in {}\n'.format(path))
            return None
        # Create job
        job = Job()
        job.type = Job.Type.PROBE
        job.info.paths = paths
        job.info.names = names
        # Register job
        DBInterface.Job.register(job)
        return str(job.guid)

