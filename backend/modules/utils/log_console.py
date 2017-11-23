# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import sys
import time
import traceback
import os
if os.name == 'nt':
    from .syslog_bulk import syslog
else:
    import syslog


class Console:
    class Colormap:
        # Color bits are (offset 0x1E):
        # bit0: RED
        # bit1: GREEN
        # bit2: BLUE
        black = 0x1E
        red = 0x1F
        green = 0x20
        yellow = 0x21
        blue = 0x22
        magenta = 0x23
        cyan = 0x24
        white = 0x25
        HIGHLIGHT = [
            [0, 0],
            [0, 1],
            [5, 1],
            [0, 7],  # not working on Windows
            [7, 1]  # not working on Windows
        ]

    @staticmethod
    def write_console_colored(string, std=sys.stderr, color=Colormap.green, invert=False, hi=1):
        # m = 0x21
        strs = string.split('\n')
        # if color in COLORMAP:
        #     m = COLORMAP[color]
        # elif type(color) is int:
        # m = 0x1E + (color % 7)
        if invert:
            color += 10
        a, b = Console.Colormap.HIGHLIGHT[hi % len(Console.Colormap.HIGHLIGHT)]
        color_str = ['\x1b[{0};{1};{2}m{3}\x1b[0m'.format(a, b, color, s) if len(s) else '' for s in strs]
        string = '\n'.join(color_str)
        std.write(string)

    @staticmethod
    def rawdemo():
        for k, i in Console.Colormap.HIGHLIGHT:
            sys.stderr.write('{0:02X}.{1:02X}: '.format(k, i))
            for j in range(30, 48):
                sys.stderr.write('\x1b[{0};{1};{2}m{2:02X}\x1b[0m '.format(k, i, j))
            sys.stderr.write('\n')


class Logger:
    class LogLevel:
        LOG_EMERG, LOG_ALERT, LOG_CRIT, LOG_ERR, LOG_WARNING, LOG_NOTICE, LOG_INFO, LOG_DEBUG = range(8)
        # DEBUG = 1
        # INFO = 2
        # LOG = 3
        TRACEBACK = 10
        TRACE = 11
        # WARNING = 5
        # ERROR = 6
        # CRITICAL = 7
        # LOG_EMERG = 8

    LOG_FILE = None
    LOG_FILE_LEVEL = LogLevel.LOG_INFO
    LOG_FILE_FORMAT      = '{{"strftime": "{ST}", "time": {T:.3f}, "level": {L}, "log": "{log}"}}\n'
    LOG_FILE_FORMAT_ARGS = '{{"strftime": "{ST}", "time": {T:.3f}, "level": {L}, "log": "{log}", "args": "{A}", "kwargs": "{K}"}}\n'

    LOG_CONSOLE = sys.stderr
    LOG_CONSOLE_LEVEL = LogLevel.LOG_DEBUG
    LOG_CONSOLE_LIKE_FILE = False

    COLOR_MAP = {
        LogLevel.LOG_DEBUG:     {'color': Console.Colormap.green, 'invert': False, 'hi': 0},
        LogLevel.LOG_INFO:     {'color': Console.Colormap.blue, 'invert': False, 'hi': 1},
        LogLevel.LOG_NOTICE:      {'color': Console.Colormap.cyan, 'invert': False, 'hi': 1},
        LogLevel.LOG_WARNING:   {'color': Console.Colormap.yellow, 'invert': False, 'hi': 1},
        LogLevel.LOG_ERR:     {'color': Console.Colormap.red, 'invert': False, 'hi': 1},
        LogLevel.LOG_CRIT:  {'color': Console.Colormap.red, 'invert': True, 'hi': 1},
        LogLevel.LOG_ALERT: {'color': Console.Colormap.magenta, 'invert': True, 'hi': 2},
        LogLevel.LOG_EMERG: {'color': Console.Colormap.cyan, 'invert': True, 'hi': 1},

        LogLevel.TRACE:     {'color': Console.Colormap.green, 'invert': False, 'hi': 1},
        LogLevel.TRACEBACK: {'color': Console.Colormap.yellow, 'invert': False, 'hi': 2},
    }

    @staticmethod
    def set_level(level):
        Logger.LOG_LEVEL = level

    @staticmethod
    def _log_file_string(string, level, *args, **kwargs):
        t = time.time()
        st = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))
        if len(args) or len(kwargs):
            return Logger.LOG_FILE_FORMAT_ARGS.format(ST=st, T=t, L=level, log=string.replace('\n', '\\n'), A=args, K=kwargs)
        return Logger.LOG_FILE_FORMAT.format(ST=st, T=t, L=level, log=string.replace('\n', '\\n'))

    @staticmethod
    def _log(string, level, colorset_level=None, *args, **kwargs):
        if colorset_level is None:
            colorset_level = level
        log_for_file = None
        if Logger.LOG_FILE_LEVEL >= level and Logger.LOG_FILE:
            log_for_file = Logger._log_file_string(string, level, *args, **kwargs)
            try:
                f = open(Logger.LOG_FILE, 'a')
                f.write(log_for_file)
                f.close()
            except:
                pass
        if Logger.LOG_CONSOLE_LEVEL >= level:
            if Logger.LOG_CONSOLE_LIKE_FILE:
                if log_for_file is None:
                    log_for_file = Logger._log_file_string(string, level, *args, **kwargs)
                Console.write_console_colored(log_for_file, **Logger.COLOR_MAP[level])
            else:
                Console.write_console_colored(string, **Logger.COLOR_MAP[colorset_level])

    @staticmethod
    def traceback():
        string = ''
        for frame in traceback.extract_tb(sys.exc_info()[2]):
            string += str(frame) + '\n'
        Logger._log(string, Logger.LogLevel.TRACEBACK)

    @staticmethod
    def trace(string, colorset_level=None, *args, **kwargs):
        Logger._log(string, Logger.LogLevel.TRACE, colorset_level, *args, **kwargs)

    @staticmethod
    def debug(string, colorset_level=None, *args, **kwargs):
        Logger._log(string, Logger.LogLevel.LOG_DEBUG, colorset_level, *args, **kwargs)

    @staticmethod
    def info(string, colorset_level=None, *args, **kwargs):
        Logger._log(string, Logger.LogLevel.LOG_INFO, colorset_level, *args, **kwargs)

    @staticmethod
    def log(string, *args, **kwargs):
        Logger._log(string, Logger.LogLevel.LOG_NOTICE, *args, **kwargs)

    @staticmethod
    def warning(string, *args, **kwargs):
        Logger._log(string, Logger.LogLevel.LOG_WARNING, *args, **kwargs)

    @staticmethod
    def error(string, *args, **kwargs):
        Logger._log(string, Logger.LogLevel.LOG_ERR, *args, **kwargs)

    @staticmethod
    def critical(string, *args, **kwargs):
        Logger._log(string, Logger.LogLevel.LOG_CRIT, *args, **kwargs)

    @staticmethod
    def exception(string, *args, **kwargs):
        Logger._log(string, Logger.LogLevel.LOG_ALERT, *args, **kwargs)

    @staticmethod
    def emergency(string, *args, **kwargs):
        Logger._log(string, Logger.LogLevel.LOG_EMERG, *args, **kwargs)


def tracer(function):
    def aux(*args, **kwargs):
        Logger.trace('trace: {F}(*a={A}, **kw={KW})\n'.format(F=function.__name__, A=args, KW=kwargs))
        return function(*args, **kwargs)
    return aux


@tracer
def test_logger(a=1, b=2, *args, **kwargs):
    Logger.trace('Trace', **{'asd': 'qwe'})
    Logger.debug('Debug')
    Logger.debug('Debug', Logger.LogLevel.LOG_ALERT)
    Logger.info('Info')
    Logger.log('Log')
    Logger.warning('Warning')
    Logger.error('Error')
    Logger.critical('Critical')
    Logger.exception('Exception')

def test():
    Logger.set_level(Logger.LogLevel.TRACE)
    Console.write_console_colored('test!\ntest1\ntest2\n', color=Console.Colormap.magenta, invert=True, hi=2)
    Console.write_console_colored('test!\ntest1\ntest2\n', color=Console.Colormap.magenta, invert=False, hi=1)
    Console.rawdemo()
    test_logger(3, 4, *(5, 6, 7), **{'asd': 'qwe'})
    Logger.LOG_CONSOLE_LIKE_FILE = True
    test_logger(3, 4, *(5, 6, 7), **{'asd': 'qwe'})
