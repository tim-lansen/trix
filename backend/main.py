# -*- coding: utf-8 -*-

# from modules.config import *
# from pprint import pprint
# from typing import List
import json

import modules.utils.combined_info
import modules.utils.types

from modules.models.record import Record
import modules.utils.class_py2coffee
from modules.models.mediafile import MediaFile

# import modules.utils.execute_chain
# from modules.config import *
# from modules.models import *
# import modules.utils.resolve_job_aliases
import modules.utils.database
# import modules.models.node
import modules.models.job
# import datetime

# import multiprocessing


if __name__ == '__main__':
    # dBase = {
    #     'templates': {},
    #     'tables': {}
    # }
    # modules.utils.database.config_table_using_class(modules.models.job.Job, dBase)
    # modules.utils.database.config_table_using_class(modules.models.asset.Asset, dBase)
    # print(json.dumps(dBase, indent=2))

    modules.utils.database.DBInterface.initialize()
    # modules.utils.database.DBInterface._drop_all_tables()

    # DBInterface.Node.records()
    # DBInterface.Node.records(Node.Status.IDLE)

    # node = modules.models.node.Node()

    # node = modules.utils.database.DBInterface.get_record_to_class('Node', '73b8af7a-72e5-40a7-a97e-1c6dac8e0f97')
    # print(node.dumps(indent=2))

    # job = Job()
    #
    # job.update_str('{"type":1,"info": {"variables": {"var1":"val1"}, "steps": [{"name": "step1", "chains": [{"progress": {"capture":0, "top": 50.0}}]}, {"name": "step2"}] }}')
    #
    # print(job.dumps())
    #
    # print(job.info.steps[0].name)
    # print(job.info.steps[0].chains[0].progress.top)


    # r = Record()
    # r.update_json({
    #     'guid': 'e5d17809-e9db-4923-a7d4-001614b998d3'
    # })
    # modules.utils.class_py2coffee.class_py2coffee(Record)
    #
    # modules.utils.class_py2coffee.class_py2coffee(MediaFile)



    # modules.utils.combined_info.test()
    # modules.utils.types.test()

    # modules.utils.execute_chain.test()

    # modules.utils.resolve_job_aliases.test()
    # modules.models.job.test()

    # job = modules.models.job.test()
    # modules.utils.database.DBInterface.Job.register(job)

    # multiprocessing.freeze_support()
    # modules.utils.execute_chain.test()
