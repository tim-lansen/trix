# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from typing import List
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

    def __init__(self, type, layout):
        super().__init__()
        self.type = None
        self.layout = None
        self.channels: List[Stream.Channel] = []
        self.language = None
        self.program_in = None
        self.program_out = None


class VideoStream(Stream):

    """
    Use stereo3d filter to convert between different stereoscopic image formats
    """

    class StereoLayoutMode:
        none  = 0
        # Input/Output stereo layouts
        sbsl  = 1   # side by side parallel (left eye left, right eye right)
        sbsr  = 2   # side by side crosseye (right eye left, left eye right)
        sbs2l = 3   # side by side parallel with half width resolution (left eye left, right eye right)
        sbs2r = 4   # side by side crosseye with half width resolution (right eye left, left eye right)
        abl   = 5   # above-below (left eye above, right eye below)
        abr   = 6   # above-below (right eye above, left eye below)
        ab2l  = 7   # above-below with half height resolution (left eye above, right eye below)
        ab2r  = 8   # above-below with half height resolution (right eye above, left eye below)
        al    = 9   # alternating frames (left eye first, right eye second)
        ar    = 10  # alternating frames (right eye first, left eye second)
        irl   = 11  # interleaved rows (left eye has top row, right eye starts on next row)
        irr   = 12  # interleaved rows (right eye has top row, left eye starts on next row)
        icl   = 13  # interleaved columns, left eye first
        icr   = 14  # interleaved columns, right eye first
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
        ml   = 29  # mono output (left eye only)
        mr   = 30  # mono output (right eye only)
        chl  = 31  # checkerboard, left eye first
        chr  = 32  # checkerboard, right eye first
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

    def __init__(self):
        super().__init__(Stream.Type.VIDEO, VideoStream.Layout.NORMAL)
        self.cropdetect = self.Cropdetect()


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
        super().__init__(Stream.Type.AUDIO, AudioStream.Layout.STEREO)


class SubStream(Stream):

    def __init__(self):
        super().__init__(Stream.Type.SUBTITLES, None)


class Asset(Record):

    class MediaFile(Guid):
        def __init__(self, v=None):
            super().__init__(v)

    def __init__(self, name=None, guid=0):
        super().__init__(name=name, guid=guid)
        # List of source media files (GUIDs)
        self.mediaFiles: List[Asset.MediaFile] = []
        # List of streams
        self.videoStreams: List[VideoStream] = []
        self.audioStreams: List[AudioStream] = []
        self.subStreams: List[SubStream] = []
        # UID of proxy asset
        self.proxyId = None
        # UID of target program (movie id, series, whatever...)
        self.programId = None

    TABLE_SETUP = {
        "relname": "trix_assets",
        "fields": [
            ["mediaFiles", "uuid[]"],
            ["videoStreams", "json"],
            ["audioStreams", "json"],
            ["subStreams", "json"],
            ["proxyId", "uuid"],
            ["programId", "uuid"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }
