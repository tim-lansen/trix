# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import re
from typing import List
from .log_console import Logger


PATTERN_TIMECODE = re.compile(r'^\d?\d:\d\d:\d\d.\d+$')


def timecode_to_float(tc):
    if type(tc) is float:
        return tc
    t = 0.0
    if PATTERN_TIMECODE.match(tc):
        i, r = tc.rsplit('.', 1)
        h, m, s = i.split(':')
        t = 60.0*(60.0*float(h) + float(m)) + float(s) + float('0.{0}'.format(r))
    return t


def split_iter(string, sep):
    ssz = len(sep)
    start = 0
    while True:
        idx = string.find(sep, start)
        if idx == -1:
            if start == 0:
                yield string
            return
        if idx > start:
            yield string[start:idx]
        start = idx + ssz


class Parsers:
    # Every parser outputs a dictionary object that may have any captured parameter
    # The mandatory value is 'pos': <float>, that represents captured time position
    PATTERN_CLEAN_FFMPEG = re.compile(r'= +')

    # Universal pattern to parse various info
    # Space filter
    PSP = re.compile(r'\s+')
    FIX = re.compile('[\\s\x08]+\]')
    # Brackets selector
    PTR = re.compile(r'\[[^@^\[\]]+\]')
    # Extract name
    PATTERN_PARSE_NAME = re.compile(r'^\[(?:Parsed_)?(\w+?)(?:_\d)? @ .+\] ')
    # Extract info
    PATTERN_PARSE_FILTER = re.compile(r' ([\w]+?)[:=]\s*([,:\.\w\[\]\(\)]+)')
    # For example
    #   "[Parsed_cropdetect_0 @ 000000000500d520] x1:0 x2:1919 t:12.513 crop=1920:1040:0:0 plane_checksum:[5DE5F53F 6479EEE4 8FAB2589] stdev:[23.7 10.5 4.6]"
    # 1. extract name: PATTERN_PARSE_NAME.findall(line)
    #    ['cropdetect']
    # 2. replace spaces: PTR.sub(lambda m: PSP.sub(',', m.group()), line)
    #   "[Parsed_cropdetect_0 @ 000000000500d520] x1:0 x2:1919 t:12.513 crop=1920:1040:0:0 plane_checksum:[5DE5F53F,6479EEE4,8FAB2589] stdev:[23.7,10.5,4.6]"
    # 3. capture info: PATTERN_PARSE_FILTER.findall(lt)
    #    [('x1', '0'), ('x2', '1919'), ('t', '12.513'), ('crop', '1920:1040:0:0'), ('plane_checksum', '[5DE5F53F,6479EEE4,8FAB2589]'), ('stdev', '[23.7,10.5,4.6]')]
    # 4.*and then dict(cap)
    #    {'x1': '0', 'x2': '1919', 't': '12.513', 'crop': '1920:1040:0:0', 'plane_checksum': '[5DE5F53F,6479EEE4,8FAB2589]', 'stdev': '[23.7,10.5,4.6]'}

    @staticmethod
    def parse_line(line):
        """
        Universal ffmpeg info parser
        :param line: a string to parse
        :return: a tuple (<info source name>, [(<key>, <val>), (<key>, <val>), ...])
        """
        # Extract name
        capture = Parsers.PATTERN_PARSE_NAME.findall(line)
        if len(capture) == 1:
            filter_name = capture[0]
            # Transform '... xxx:[aaa bbb ccc] ...' => '... xxx:[aaa,bbb,ccc] ...'
            lt = Parsers.PTR.sub(lambda m: Parsers.PSP.sub(',', m.group()), Parsers.FIX.sub(']', line))
            # Capture info
            capture = Parsers.PATTERN_PARSE_FILTER.findall(lt)
            if len(capture) > 0:
                return filter_name, capture
        return None, None

    @staticmethod
    def parse_auto(line):
        """
        Auto-select handler
        :param line: a string to parse
        :return: tuple (<handler>, <handler output>)
        """
        if type(line) is bytes:
            line = line.decode()
        if line.startswith('frame=') or line.startswith('size='):
            fc = Parsers.ffmpeg_progress(line)
            if fc:
                return 'progress', fc
            return None, None
        fn, fc = Parsers.parse_line(line.strip())
        if fn:
            if fn in PARSERS_VECTORS:
                return fn, PARSERS_VECTORS[fn](fc)
            else:
                return fn, dict(fc)
        return None, None

    @staticmethod
    def ffmpeg_auto_text(text):
        parsed = {}
        for line in split_iter(text, '\n'):
            fn, fc = Parsers.parse_line(line.strip())
            if fn:
                if fn not in parsed:
                    parsed[fn] = []
                parsed[fn].append(dict(fc))
        return parsed

    @staticmethod
    def ffmpeg_cropdetect(cap):
        if type(cap) is str:
            fn, cap = Parsers.parse_line(cap)
            if fn != 'cropdetect':
                return None
        cap = dict(cap)
        res = {}
        try:
            x1, x2, y1, y2 = int(cap['x1']), int(cap['x2']), int(cap['y1']), int(cap['y2'])
            if x2 > x1:
                res.update({'x': x1, 'w': x2 + 1 - x1})
            if y2 > y1:
                res.update({'y': y1, 'h': y2 + 1 - y1})
            res['pts'] = int(cap['pts'])
        except KeyError as e:
            Logger.warning(str(e), **cap)
        except ValueError as e:
            Logger.warning(str(e), **cap)
        if len(res) < 3:
            Logger.warning('Cropdetect info ignored completely\n', **cap)
            return None
        return res

    @staticmethod
    def ffmpeg_showinfo(fc):
        si = dict(fc)
        if 'n' in si:
            return si
        return None

    @staticmethod
    def ffmpeg_progress(line):
        line = Parsers.PATTERN_CLEAN_FFMPEG.sub('=', line)
        d = None
        try:
            d = {k: v for k, v in [p.split('=') for p in line.split(' ') if '=' in p]}
            if 'fps' in d:
                d['fps'] = float(d['fps'])
            # if 'time' in d:
            #     d['pos'] = timecode_to_float(d['time'])
        except:
            pass
        return d


PARSERS_VECTORS = {
    'cropdetect': Parsers.ffmpeg_cropdetect,
    'showinfo': Parsers.ffmpeg_showinfo
}


PARSERS = {
    'ffmpeg_auto_text': Parsers.ffmpeg_auto_text,
    'ffmpeg_progress': Parsers.ffmpeg_progress,
    'ffmpeg_cropdetect': Parsers.ffmpeg_cropdetect,
}


def parse_text(text, parser):
    res = []
    if parser in PARSERS:
        par = PARSERS[parser]
        for line in split_iter(text, '\n'):
            p = par(line)
            if p:
                res.append(p)
    return res

