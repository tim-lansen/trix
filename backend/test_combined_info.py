# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import sys
from modules.utils.log_console import Logger
from modules.utils.combined_info import test


if __name__ == '__main__':
    Logger.info('Running  modules.utils.combined_info.test()\n')
    test(None if len(sys.argv) == 1 else sys.argv[1:])
    Logger.info('Done\n')
