# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import re
from typing import List


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
    # Universal pattern to parse various info
    # For example
    # "[Parsed_cropdetect_0 @ 000000000500d520] x1:0 x2:1919 y1:0 y2:1039 w:1920 h:1040 x:0 y:0 pts:12513 t:12.513000 crop=1920:1040:0:0"
    # becomes
    # [('x1', '0'), ('x2', '1919'), ('y1', '0'), ('y2', '1039'), ('w', '1920'), ('h', '1040'), ('x', '0'), ('y', '0'), ('pts', '12513'), ('t', '12.513000'), ('crop', '1920:1040:0:0')]
    # and then dict()
    # {'x1': '0', 'x2': '1919', 'y1': '0', 'y2': '1039', 'w': '1920', 'h': '1040', 'x': '0', 'y': '0', 'pts': '12513', 't': '12.513000', 'crop': '1920:1040:0:0'}
    PATTERN_PARSE_FILTER = re.compile(r' ([\w]+?)[:=]([\d\.:]+)')

    # HOW TO PARSE "... plane_checksum:[5DE5F53F 6479EEE4 8FAB2589] mean:[51 144 125] stdev:[23.7 10.5 4.6]"

    # PATTERN_PARSE_NAME = re.compile(r'^\[(\w+) @ .+\] ')
    # From
    # "[Parsed_cropdetect_0 @ 000000000500d520] ....."
    # captures ['cropdetect']
    PATTERN_PARSE_NAME = re.compile(r'^\[(?:Parsed_)?(\w+?)(?:_\d)? @ .+\] ')

    @staticmethod
    def parse_line(line, result: List[tuple]):
        capture = Parsers.PATTERN_PARSE_NAME.findall(line)
        if len(capture) == 1:
            filter_name = capture[0]
            capture = Parsers.PATTERN_PARSE_FILTER.findall(line)
            if len(capture) == 1:
                result.append((filter_name, capture))
                return True
        return False

    @staticmethod
    def parse_auto(line):
        p = []
        if Parsers.parse_line(line, p):
            if p[0] in Parsers.VECTORS:
                return Parsers.VECTORS[p[0]](dict(p[1]))
        return None

    @staticmethod
    def ffmpeg_cropdetect(line):
        l = line
        if type(line) is str:
            p = []
            if not Parsers.parse_line(line, p):
                return None
            if p[0] != 'cropdetect':
                return None
            l = dict(p[1])
        res = {}
        try:
            x1, x2, y1, y2 = [int(l['x1']), int(l['x2']), int(l['y1']), int(l['y2'])]
            if x2 > x1:
                res.update({'x': x1, 'w': x2 + 1 - x1})
            if y2 > y1:
                res.update({'y': y1, 'h': y2 + 1 - y1})
        except:
            return None
        if len(res) == 0:
            return None
        res['pts'] = int(l['pts'])
        return res

    @staticmethod
    def ffmpeg_showinfo():
        return None

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

    VECTORS = {
        'cropdetect': ffmpeg_cropdetect,
        'showinfo': ffmpeg_showinfo
    }


PARSERS = {
    'ffmpeg': Parsers.parser_ffmpeg
}



