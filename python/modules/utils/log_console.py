# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import sys


# Color bits are (offset 0x1E):
# bit0: RED
# bit1: GREEN
# bit2: BLUE


COLORMAP = {
    'black'  : 0x1E,
    'red'    : 0x1F,
    'green'  : 0x20,
    'yellow' : 0x21,
    'blue'   : 0x22,
    'magenta': 0x23,
    'cyan'   : 0x24,
    'white'  : 0x25
}


HIGHLIGHT = [
    [0, 0],
    [0, 1],
    [5, 1],
    [0, 7],     # not working on Windows
    [7, 1]      # not working on Windows
]


def rawdemo():
    for k, i in HIGHLIGHT:
        sys.stderr.write('{0:02X}.{1:02X}: '.format(k, i))
        for j in range(30, 48):
            sys.stderr.write('\x1b[{0};{1};{2}m{2:02X}\x1b[0m '.format(k, i, j))
        sys.stderr.write('\n')


def write_console_colored(string, std=sys.stderr, color='green', invert=False, hi=1):
    m = 0x21
    strs = string.split('\n')
    if color in COLORMAP:
        m = COLORMAP[color]
    elif type(color) is int:
        m = 0x1E + (color % 7)
    if invert:
        m += 10
    a, b = HIGHLIGHT[hi % len(HIGHLIGHT)]
    color_str = ['\x1b[{0};{1};{2}m{3}\x1b[0m'.format(a, b, m, s) if len(s) else '' for s in strs]
    string = '\n'.join(color_str)
    std.write(string)
    # std.write('\x1b[{0};{1};{2}m{3}\x1b[0m'.format(a, b, m, string))


class DebugLevel:
    TRACE = 0
    DEBUG = 1
    INFO = 2
    LOG = 3
    WARNING = 4
    ERROR = 5
    CRITICAL = 6
    EXCEPTION = 7


class Logger:
    DEBUG_LEVEL = DebugLevel.DEBUG
    COLOR_MAP = {
        DebugLevel.TRACE:     {'color': 'green',   'invert': False, 'hi': 0},
        DebugLevel.DEBUG:     {'color': 'green',   'invert': False, 'hi': 1},
        DebugLevel.INFO:      {'color': 'cyan',    'invert': False, 'hi': 1},
        DebugLevel.LOG:       {'color': 'white',   'invert': False, 'hi': 0},
        DebugLevel.WARNING:   {'color': 'yellow',  'invert': False, 'hi': 1},
        DebugLevel.ERROR:     {'color': 'red',     'invert': False, 'hi': 1},
        DebugLevel.CRITICAL:  {'color': 'red',     'invert': True,  'hi': 2},
        DebugLevel.EXCEPTION: {'color': 'magenta', 'invert': True, 'hi': 2},
    }

    @staticmethod
    def set_level(level):
        Logger.DEBUG_LEVEL = level

    @staticmethod
    def _log(string, level):
        if Logger.DEBUG_LEVEL <= level:
            write_console_colored(string, **Logger.COLOR_MAP[level])

    @staticmethod
    def trace(string):
        Logger._log(string, DebugLevel.TRACE)

    @staticmethod
    def debug(string):
        Logger._log(string, DebugLevel.DEBUG)

    @staticmethod
    def info(string):
        Logger._log(string, DebugLevel.INFO)

    @staticmethod
    def log(string):
        Logger._log(string, DebugLevel.LOG)

    @staticmethod
    def warning(string):
        Logger._log(string, DebugLevel.WARNING)

    @staticmethod
    def error(string):
        Logger._log(string, DebugLevel.ERROR)

    @staticmethod
    def critical(string):
        Logger._log(string, DebugLevel.CRITICAL)

    @staticmethod
    def exception(string):
        Logger._log(string, DebugLevel.EXCEPTION)


def tracer(function):
    def aux(*args, **kwargs):
        Logger.trace('trace {0}\n'.format(function))
        return function(*args, **kwargs)
    return aux


@tracer
def test_logger():
    Logger.trace('Trace')
    Logger.debug('Debug')
    Logger.info('Info')
    Logger.log('Log')
    Logger.warning('Warning')
    Logger.error('Error')
    Logger.critical('Critical')
    Logger.exception('Exception')


if __name__ == '__main__':
    Logger.set_level(DebugLevel.TRACE)
    write_console_colored('test!\ntest1\ntest2\n', color='magenta', invert=True, hi=2)
    write_console_colored('test!\ntest1\ntest2\n', color='magenta', invert=False, hi=1)
    rawdemo()
    test_logger()

