# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import sys


class syslog:
    LOG_EMERG, LOG_ALERT, LOG_CRIT, LOG_ERR, LOG_WARNING, LOG_NOTICE, LOG_INFO, LOG_DEBUG = range(8)

    LOG_KERN, LOG_USER, LOG_MAIL, LOG_DAEMON, LOG_AUTH, LOG_SYSLOG, LOG_LPR, LOG_NEWS, LOG_UUCP = range(0, 65, 8)

    LOG_CRON = 120
    LOG_LOCAL0 = 128
    LOG_LOCAL1 = 136
    LOG_LOCAL2 = 144
    LOG_LOCAL3 = 152
    LOG_LOCAL4 = 160
    LOG_LOCAL5 = 168
    LOG_LOCAL6 = 176
    LOG_LOCAL7 = 184

    LOG_PID = 1
    LOG_CONS = 2
    LOG_NDELAY = 8
    LOG_NOWAIT = 16

    @staticmethod
    def syslog(message):
        pass

    @staticmethod
    def syslog(priority, message):
        pass

    @staticmethod
    def openlog(ident=sys.argv[0], logoptions=0, facility=LOG_USER):
        pass

    @staticmethod
    def closelog():
        pass

    @staticmethod
    def setlogmask(maskpri):
        pass
