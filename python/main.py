# -*- coding: utf-8 -*-

import json
from pprint import pprint
from typing import List
import modules.utils.combined_info
import modules.utils.execute_chain
# from modules.config import *
from modules.models import *
import modules.utils.resolve_job_aliases


# DBInterface.initialize()
# print(DBInterface.Node.register('node 2', Node.Status.IDLE))
# print(DBInterface.Node.register('node 1', Node.Status.BUSY))

# DBInterface.Node.records()
# DBInterface.Node.records(Node.Status.IDLE)


# job = Job()
#
# job.update_str('{"type":1,"info": {"variables": {"var1":"val1"}, "steps": [{"name": "step1", "chains": [{"progress": {"capture":0, "top": 50.0}}]}, {"name": "step2"}] }}')
#
# print(job.dumps())
#
# print(job.info.steps[0].name)
# print(job.info.steps[0].chains[0].progress.top)

# modules.utils.combined_info.test()

# modules.utils.execute_chain.test()

modules.utils.resolve_job_aliases.test()
