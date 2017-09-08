# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


from modules.utils.log_console import Logger
from modules.utils.executor import test, test_combined_info


if __name__ == '__main__':
    Logger.info('Running  modules.utils.executor.test()\n')
    test()
    # test_combined_info()
    Logger.info('Done\n')
