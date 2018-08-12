#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import os
import sys
from modules.utils.job_utils import JobUtils


if __name__ == '__main__':
    if os.path.isdir(sys.argv[1]):
        JobUtils.CreateJob.ingest_prepare_sliced(sys.argv[1])

