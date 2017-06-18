# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from typing import List
from modules.models.record import *


class Stream(JSONer):
    class Type:
        VIDEO = 0
        AUDIO = 1
        SUBTITLES = 2

    class Source(JSONer):
        def __init__(self):
            super().__init__()
            self.mediaFileId = None
            self.streamIndexOfType = None
            self.streamChannel = 0

    def __init__(self):
        super().__init__()
        self.type = None
        self.layout = None
        self.sources: List[Stream.Source] = []
        self.language = None


class VideoStream(Stream):
    class Layout:
        NORMAL = 0
        STEREO = 1
        PANORAMIC = 2

    def __init__(self):
        super().__init__()


class AudioStream(Stream):
    class Layout:
        MONO = 0
        STEREO = 1
        SURROUND51 = 2

    def __init__(self):
        super().__init__()


class SubStream(Stream):

    def __init__(self):
        super().__init__()


class Asset(Record):

    def __init__(self):
        super().__init__()
        # List of streams
        self.videoStreams: List[VideoStream] = []
        self.audioStreams: List[AudioStream] = []
        self.subStreams: List[SubStream] = []
        # UID of proxy asset
        self.proxyId = None
        # UID of target program (movie id, series, whatever...)
        self.programId = None

