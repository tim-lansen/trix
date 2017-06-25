# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import re


PATTERN_TIMECODE = re.compile(r'^\d?\d:\d\d:\d\d.\d+$')
def timecode_to_float(tc):
    t = 0.0
    if PATTERN_TIMECODE.match(tc):
        i, r = tc.rsplit('.', 1)
        h, m, s = i.split(':')
        t = 60.0*(60.0*float(h) + float(m)) + float(s) + float('0.{0}'.format(r))
    return t


class Parsers:
    # Every parser outputs a dictionary object that may have any captured parameter
    # The mandatory value is 'pos': <float>, that represents captured time position
    PATTERN_CLEAN_FFMPEG = re.compile(r'= +')

    @staticmethod
    def parser_ffmpeg(line):
        line = Parsers.PATTERN_CLEAN_FFMPEG.sub('=', line)
        d = None
        try:
            d = {k: v for k, v in [p.split('=') for p in line.split(' ') if '=' in p]}
            if 'fps' in d:
                d['fps'] = float(d['fps'])
            if 'time' in d:
                d['pos'] = timecode_to_float(d['time'])
        except:
            pass
        return d


PARSERS = {
    'ffmpeg': Parsers.parser_ffmpeg
}



