# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


from modules.utils.log_console import Logger
from modules.utils.executor import test, test_combined_info


if __name__ == '__main__':
    Logger.debug('Running  modules.utils.executor.test()\n', Logger.LogLevel.LOG_INFO)
    test()
    # test_combined_info()
    Logger.debug('Done\n', Logger.LogLevel.LOG_INFO)
