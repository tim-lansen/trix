# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import os
import sys
from modules.models import *
from ..utils.log_console import Logger, LogLevel, tracer
from ..utils.jsoner import JSONer


class TrixConfig(JSONer):
    class DBase(JSONer):
        class Connection(JSONer):
            def __init__(self):
                super().__init__()
                self.host = None
                self.port = None
                self.dbname = None

        def __init__(self):
            super().__init__()
            self.connection = self.Connection()
            self.users = None
            self.tables = None
            self.templates = None

        def conform_tables(self):
            # Update tables that use template
            if type(self.tables) is dict:
                for table_name in self.tables:
                    table = self.tables[table_name]
                    try:
                        template = self.templates[table['template']]
                        for key in template:
                            val = template[key]
                            if key not in table:
                                table[key] = val
                            else:
                                if type(val) is list:
                                    table[key] = val + table[key]
                                else:
                                    Logger.error("Table template value type {} not supported\n".format(type(val)))
                    except Exception as e:
                        Logger.warning("Table {} template error\n{}\n".format(table_name, e))

    class ApiServer(JSONer):
        def __init__(self):
            super().__init__()
            self.host = None
            self.port = None

    class Machines(JSONer):
        def __init__(self):
            super().__init__()
            self.comment = None
            self.default = None

    def __init__(self):
        super().__init__()
        self.dBase = self.DBase()
        self.apiServer = self.ApiServer()
        self.machines = self.Machines()


TRIX_CONFIG = TrixConfig()


# Read trix_config.json
with open(os.path.join(os.path.dirname(__file__), 'trix_config.json'), 'r') as config_file:
    config_string = config_file.read()
    TRIX_CONFIG.update_str(config_string)
    TRIX_CONFIG.dBase.conform_tables()


# Check that tables config equals class definitions
def check_config_conformity():

    def str_to_class(s):
        if s in globals():
            gc = globals()[s]
            if isinstance(gc, type(object)):
                return gc
        return None

    failed = False
    for t in TRIX_CONFIG.dBase.tables:
        c = str_to_class(t)
        if c is None:
            Logger.warning('No python model found for table {}\n'.format(t))
            continue
        ct = TRIX_CONFIG.dBase.tables[t]
        cfields = {f[0] for f in ct['fields']}
        pfields = c().get_members_set()
        diff = cfields.symmetric_difference(pfields)
        if len(diff):
            Logger.error('{table}: config and code not conformed, check these members/fields:\n{fields}\n'.format(table=t, fields=' '.join(diff)))
            failed = True
    if failed:
        Logger.critical('check_config_conformity failed, exiting\n')
        sys.exit(1)
    Logger.info('check_config_conformity passed\n')


check_config_conformity()


if __name__ == '__main__':
    import pprint
    pprint.pprint(TRIX_CONFIG.dBase.__dict__)
