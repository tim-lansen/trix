# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import os
from typing import List
from modules.utils.types import Rational
from modules.models.record import *


class Stream(JSONer):
    class Type:
        VIDEO = 0
        AUDIO = 1
        SUBTITLES = 2

    class Channel(JSONer):
        def __init__(self):
            super().__init__()
            self.src_stream_index = 0
            self.src_channel_index = 0

    class Sync(JSONer):
        def __init__(self):
            super().__init__()
            self.offset1 = None
            self.offset2 = None
            self.delay1 = None
            self.delay2 = None

    class Collector(Guid):
        def __init__(self, value=None):
            super().__init__(value)

    def __init__(self, type, layout):
        super().__init__()
        self.type = None
        self.layout = None
        self.channels: List[Stream.Channel] = []
        self.language = None
        self.program_in = None
        self.program_out = None
        self.sync: self.Sync = self.Sync()
        self.collector: self.Collector = self.Collector()


class Asset(Record):
    class VideoStream(Stream):
        """
        Use stereo3d filter to convert between different stereoscopic image formats
        """

        class StereoLayoutMode:
            none = 0
            # Input/Output stereo layouts
            sbsl = 1  # side by side parallel (left eye left, right eye right)
            sbsr = 2  # side by side crosseye (right eye left, left eye right)
            sbs2l = 3  # side by side parallel with half width resolution (left eye left, right eye right)
            sbs2r = 4  # side by side crosseye with half width resolution (right eye left, left eye right)
            abl = 5  # above-below (left eye above, right eye below)
            abr = 6  # above-below (right eye above, left eye below)
            ab2l = 7  # above-below with half height resolution (left eye above, right eye below)
            ab2r = 8  # above-below with half height resolution (right eye above, left eye below)
            al = 9  # alternating frames (left eye first, right eye second)
            ar = 10  # alternating frames (right eye first, left eye second)
            irl = 11  # interleaved rows (left eye has top row, right eye starts on next row)
            irr = 12  # interleaved rows (right eye has top row, left eye starts on next row)
            icl = 13  # interleaved columns, left eye first
            icr = 14  # interleaved columns, right eye first
            # Output stereo layouts
            arbg = 15  # anaglyph red/blue gray (red filter on left eye, blue filter on right eye)
            argg = 16  # anaglyph red/green gray (red filter on left eye, green filter on right eye)
            arcg = 17  # anaglyph red/cyan gray (red filter on left eye, cyan filter on right eye)
            arch = 18  # anaglyph red/cyan half colored (red filter on left eye, cyan filter on right eye)
            arcc = 19  # anaglyph red/cyan color (red filter on left eye, cyan filter on right eye)
            arcd = 20  # anaglyph red/cyan color optimized with the least squares projection of dubois (red filter on left eye, cyan filter on right eye)
            agmg = 21  # anaglyph green/magenta gray (green filter on left eye, magenta filter on right eye)
            agmh = 22  # anaglyph green/magenta half colored (green filter on left eye, magenta filter on right eye)
            agmc = 23  # anaglyph green/magenta colored (green filter on left eye, magenta filter on right eye)
            agmd = 24  # anaglyph green/magenta color optimized with the least squares projection of dubois (green filter on left eye, magenta filter on right eye)
            aybg = 25  # anaglyph yellow/blue gray (yellow filter on left eye, blue filter on right eye)
            aybh = 26  # anaglyph yellow/blue half colored (yellow filter on left eye, blue filter on right eye)
            aybc = 27  # anaglyph yellow/blue colored (yellow filter on left eye, blue filter on right eye)
            aybd = 28  # anaglyph yellow/blue color optimized with the least squares projection of dubois (yellow filter on left eye, blue filter on right eye)
            ml = 29  # mono output (left eye only)
            mr = 30  # mono output (right eye only)
            chl = 31  # checkerboard, left eye first
            chr = 32  # checkerboard, right eye first
            hdmi = 33  # HDMI frame pack

        class Layout:
            NORMAL = 1
            STEREO = 2
            PANORAMIC = 3

        class Cropdetect(JSONer):
            """
            Automatic cropdetect
            """
            def __init__(self):
                super().__init__()
                self.w = None
                self.h = None
                self.x = None
                self.y = None
                self.sar = None
                self.aspect = None

            def filter_string(self):
                if self.w is None or self.h is None or self.x is None or self.y is None:
                    return None
                if self.w < 0:
                    self.w = -self.w
                    self.x -= self.w
                if self.h < 0:
                    self.h = -self.h
                    self.y -= self.h
                return 'crop=w={}:h={}:x={}:y={}'.format(self.w, self.h, self.x, self.y)

        class FpsOriginal(Rational):
            def __init__(self, *args):
                super().__init__(*args)

        class FpsEncode(Rational):
            def __init__(self, *args):
                super().__init__(*args)

        def __init__(self):
            super().__init__(Stream.Type.VIDEO, Asset.VideoStream.Layout.NORMAL)
            self.cropdetect = self.Cropdetect()
            self.fpsOriginal: self.FpsOriginal = self.FpsOriginal()
            self.fpsEncode: self.FpsEncode = self.FpsEncode()

    class AudioStream(Stream):
        class Layout:
            # TODO: full set of audio layouts
            INVALID = 0
            MONO = 'mono'
            STEREO = 'stereo'
            STEREO_LFE = '2.1'
            QUADRO = '4.0'
            QUADRO_LFE = '4.1'
            SURROUND_51 = '5.1'

            # From Interaction.AudioMan
            LAYOUTS = [
                {'code': 'mono', 'name': 'Mono', 'layout': ['FC']},
                {'code': 'stereo', 'name': 'Stereo', 'layout': ['FL', 'FR']},
                {'code': '2.1', 'name': '2.1', 'layout': ['FL', 'FR', 'LFE']},
                {'code': '3.0', 'name': '3.0', 'layout': ['FL', 'FR', 'FC']},
                # {'code': '3.0(back)',      'name': '3.0 (back)',      'layout': ['FL',  'FR',  'BC']},
                {'code': '4.0', 'name': '4.0', 'layout': ['FL', 'FR', 'FC', 'BC']},
                {'code': 'quad', 'name': 'Quadro', 'layout': ['FL', 'FR', 'BL', 'BR']},
                # {'code': 'quad(side)',     'name': 'Quadro (side)',   'layout': ['FL',  'FR',  'SL',  'SR']},
                {'code': '3.1', 'name': '3.1', 'layout': ['FL', 'FR', 'FC', 'LFE']},
                # {'code': '5.0',            'name': '5.0 (back)',      'layout': ['FL',  'FR',  'FC',  'BL',  'BR']},
                {'code': '5.0(side)', 'name': '5.0 (side)', 'layout': ['FL', 'FR', 'FC', 'SL', 'SR']},
                {'code': '4.1', 'name': '4.1', 'layout': ['FL', 'FR', 'FC', 'LFE', 'BC']},
                {'code': '5.1', 'name': '5.1', 'layout': ['FL', 'FR', 'FC', 'LFE', 'BL', 'BR']},
                {'code': '5.1(side)', 'name': '5.1 (side)', 'layout': ['FL',  'FR',  'FC',  'LFE', 'SL',  'SR']},
                {'code': '6.0', 'name': '6.0', 'layout': ['FL', 'FR', 'FC', 'BC', 'SL', 'SR']},
                # {'code': '6.0(front)',     'name': '6.0 (front)',     'layout': ['FL',  'FR',  'FLC', 'FRC', 'SL',  'SR']},
                {'code': 'hexagonal', 'name': 'Hexagonal', 'layout': ['FL', 'FR', 'FC', 'BL', 'BR', 'BC']},
                # {'code': '6.1',            'name': '6.1 (side)',      'layout': ['FL',  'FR',  'FC',  'LFE', 'BC',  'SL',  'SR']},
                {'code': '6.1', 'name': '6.1', 'layout': ['FL', 'FR', 'FC', 'LFE', 'BL', 'BR', 'BC']},
                {'code': '6.1(front)', 'name': '6.1 (front)', 'layout': ['FL', 'FR', 'LFE', 'FLC', 'FRC', 'SL', 'SR']},
                {'code': '7.0', 'name': '7.0', 'layout': ['FL', 'FR', 'FC', 'BL', 'BR', 'SL', 'SR']},
                # {'code': '7.0(front)',     'name': '7.0 (front)',     'layout': ['FL',  'FR',  'FC',  'FLC', 'FRC', 'SL',  'SR']},
                {'code': '7.1', 'name': '7.1', 'layout': ['FL', 'FR', 'FC', 'LFE', 'BL', 'BR', 'SL', 'SR']},
                # {'code': '7.1(wide)',      'name': '7.1 (wide)',      'layout': ['FL',  'FR',  'FC',  'LFE', 'BL',  'BR',  'FLC', 'FRC']},
                # {'code': '7.1(wide-side)', 'name': '7.1 (wide-side)', 'layout': ['FL',  'FR',  'FC',  'LFE', 'FLC', 'FRC', 'SL',  'SR']},
                {'code': 'octagonal', 'name': 'Octagonal', 'layout': ['FL', 'FR', 'FC', 'BL', 'BR', 'BC', 'SL', 'SR']},
                # {'code': 'downmix',        'name': 'Downmix',         'layout': ['DL',  'DR']}
            ]

            LAYMAP = {_['code']: _ for _ in LAYOUTS}

            DEFAULT = [
                INVALID,
                MONO,
                STEREO,
                STEREO_LFE,
                QUADRO,
                QUADRO_LFE,
                SURROUND_51
            ]

        def __init__(self):
            super().__init__(Stream.Type.AUDIO, Asset.AudioStream.Layout.STEREO)

    class SubStream(Stream):
        def __init__(self):
            super().__init__(Stream.Type.SUBTITLES, None)

    class MediaFile(Guid):
        def __init__(self, v=None):
            super().__init__(v)

    class MediaFileExtra(Guid):
        def __init__(self, v=None):
            super().__init__(v)

    class TaskId(Guid):
        def __init__(self, v=None):
            super().__init__(v)

    def __init__(self, program_name='', name=None, guid=0, task_id=None):
        super().__init__(name=name, guid=guid)
        # List of source media files (GUIDs)
        self.mediaFiles: List[Asset.MediaFile] = []
        self.mediaFilesExtra: List[Asset.MediaFileExtra] = []
        # List of streams
        self.videoStreams: List[Asset.VideoStream] = []
        self.audioStreams: List[Asset.AudioStream] = []
        self.subStreams: List[Asset.SubStream] = []
        # UID of related task
        self.taskId: Asset.TaskId = Asset.TaskId(task_id)
        # UID of proxy asset
        self.proxyId = None
        # UID of target program (movie id, series, whatever...)
        self.programId = None
        # Name of program (not exact, but mandatory)
        self.programName = program_name
        if os.path.sep in program_name:
            self.program_name_by_path(program_name)

    def __str__(self):
        return self.dumps(indent=2)

    def program_name_by_path(self, path: str):
        x = path.rsplit(os.path.sep, 2)
        if len(x) > 1:
            x = x[1:]
        self.programName = ': '.join(x).rsplit('.', 1)[0]

    def full_instance(self):
        self.guid.set(None)
        self.videoStreams = [Asset.VideoStream()]
        self.audioStreams = [Asset.AudioStream()]
        self.subStreams = [Asset.SubStream()]
        self.proxyId = Guid()
        self.programId = Guid()

    TABLE_SETUP = {
        "relname": "trix_assets",
        "fields": [
            ["mediaFiles", "uuid[]"],
            ["mediaFilesExtra", "uuid[]"],
            ["videoStreams", "json[]"],
            ["audioStreams", "json[]"],
            ["subStreams", "json[]"],
            ["taskId", "uuid"],
            ["proxyId", "uuid"],
            ["programId", "uuid"],
            ["programName", "name"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }
