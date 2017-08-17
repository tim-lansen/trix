# -*- coding: utf-8 -*-

import modules.utils.database
import modules.models.job


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

