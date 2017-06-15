# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import os
import sys
from ..utils.log_console import Logger, DebugLevel, tracer
from ..utils.jsoner import JSONer


class ConfigConnection(JSONer):
    def __init__(self):
        super().__init__()
        self.host = None
        self.port = None
        self.dbname = None


class ConfigDBase(JSONer):
    def __init__(self):
        super().__init__()
        self.connection = ConfigConnection()
        self.users = None
        self.tables = None


class ApiServer(JSONer):
    def __init__(self):
        super().__init__()
        self.host = None
        self.port = None


class TrixConfig(JSONer):
    def __init__(self):
        super().__init__()
        self.dbase = ConfigDBase()
        self.api_server = ApiServer()


TRIX_CONFIG = TrixConfig()


# Read trix_config.json
with open(os.path.join(os.path.dirname(__file__), 'trix_config.json'), 'r') as config_file:
    config_string = config_file.read()
    TRIX_CONFIG.update_str(config_string)


# Check that tables config equals class definitions
def check_config_conformity():

    def str_to_class(s):
        if s in globals():
            c = globals()[s]
            if isinstance(c, type(object)):
                return c
        return None

    failed = False
    for t in TRIX_CONFIG.dbase.tables:
        c = str_to_class(t)
        if c is None:
            Logger.warning('No python model found for table {}\n'.format(t))
            continue
        ct = TRIX_CONFIG.dbase.tables[t]
        cfields = {f[0] for f in ct['fields']}
        pfields = c().get_members()
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
    pprint.pprint(TRIX_CONFIG.dbase.__dict__)
