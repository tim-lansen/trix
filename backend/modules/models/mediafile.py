# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from typing import List
from modules.models.record import *
from modules.utils.types import Rational


class MediaFile(Record):
    # MediaFile may be a single file, or a sequence of chunks
    class Source(JSONer):
        def __init__(self):
            super().__init__()
            # File path in case of single-file access
            self.path = None
            # File URL for external access
            self.url = None
            # List of chunks IDs
            self.chunks = None

    class Format(JSONer):
        class Tags(JSONer):
            def __init__(self):
                super().__init__()
                self.encoder = None
                self.creation_time = None

        # class MiFormat(JSONer):
        #     def __init__(self):
        #         super().__init__()
        #         # Count                            : 325
        #         # StreamCount                      : 1
        #         # StreamKind                       : General
        #         # StreamKind/String                : General
        #         # StreamKindID                     : 0
        #         # UniqueID                         : 184990659868305317247132685773812810764
        #         # UniqueID/String                  : 184990659868305317247132685773812810764 (0x8B2BE7B66B159612B9D1A62B7D78440C)
        #         self.VideoCount = None
        #         self.AudioCount = None
        #         self.TextCount = None
        #         # Video_Format_List                : AVC
        #         # Video_Format_WithHint_List       : AVC
        #         # Video_Codec_List                 : AVC
        #         # Video_Language_List              : en
        #         # Audio_Format_List                : AAC / AC-3
        #         # Audio_Format_WithHint_List       : AAC / AC-3
        #         # Audio_Codec_List                 : AAC LC / AC3
        #         # Audio_Language_List              : ru / en
        #         # Text_Format_List                 : UTF-8 / UTF-8 / UTF-8
        #         # Text_Format_WithHint_List        : UTF-8 / UTF-8 / UTF-8
        #         # Text_Codec_List                  : UTF-8 / UTF-8 / UTF-8
        #         # Text_Language_List               : ru / ru / en
        #         # CompleteName                     : F:\Kinozal\the.pixar.story.bluray.720p.x264.RUS.mkv
        #         # FolderName                       : F:\Kinozal
        #         # FileName                         : the.pixar.story.bluray.720p.x264.RUS
        #         # FileExtension                    : mkv
        #         # Format                           : Matroska
        #         self.Format_String = None
        #         # Format/Url                       : http://packs.matroska.org/
        #         # Format/Extensions                : mkv mk3d mka mks
        #         # Format_Commercial                : Matroska
        #         # Format_Version                   : Version 2
        #         # Codec                            : Matroska
        #         # Codec/String                     : Matroska
        #         # Codec/Url                        : http://packs.matroska.org/
        #         # Codec/Extensions                 : mkv mk3d mka mks
        #         self.FileSize = None
        #         # FileSize/String                  : 1.69 GiB
        #         # FileSize/String1                 : 2 GiB
        #         # FileSize/String2                 : 1.7 GiB
        #         # FileSize/String3                 : 1.69 GiB
        #         # FileSize/String4                 : 1.690 GiB
        #         self.duration = None
        #         # Duration/String                  : 1h 28mn
        #         # Duration/String1                 : 1h 28mn 38s 869ms
        #         # Duration/String2                 : 1h 28mn
        #         # Duration/String3                 : 01:28:38.869
        #         # Duration/String4                 : 01:28:40;05
        #         # Duration/String5                 : 01:28:38.869 (01:28:40;05)
        #         self.OverallBitRate = None
        #         # OverallBitRate/String            : 2729 Kbps
        #         # FrameRate                        : 23.976
        #         # FrameRate/String                 : 23.976 fps2
        #         # FrameCount                       : 127525
        #         # Encoded_Date                     : UTC 2011-12-02 14:56:33
        #         # File_Created_Date                : UTC 2016-01-22 19:33:00.750
        #         # File_Created_Date_Local          : 2016-01-22 22:33:00.750
        #         # File_Modified_Date               : UTC 2016-01-22 20:18:46.314
        #         # File_Modified_Date_Local         : 2016-01-22 23:18:46.314
        #         # Encoded_Application              : mkvmerge v4.9.1 ('Ich will') сборка от Jul 11 2011 23:53:15
        #         # Encoded_Application/String       : mkvmerge v4.9.1 ('Ich will') сборка от Jul 11 2011 23:53:15
        #         # Encoded_Library                  : libebml v1.2.1 + libmatroska v1.1.1
        #         # Encoded_Library/String           : libebml v1.2.1 + libmatroska v1.1.1
        #
        # class FfFormat(JSONer):
        #     def __init__(self):
        #         super().__init__()
        #         # "filename": "F:\\Kinozal\\the.pixar.story.bluray.720p.x264.RUS.mkv",
        #         self.nb_streams = None
        #         self.nb_programs = None
        #         # "format_name": "matroska,webm",
        #         # "format_long_name": "Matroska / WebM",
        #         self.start_time = None
        #         self.duration = None
        #         # "size": "1814335252",
        #         # "bit_rate": "2728903",
        #         # "probe_score": 100,
        #         # "tags": {
        #         #     "encoder": "libebml v1.2.1 + libmatroska v1.1.1",
        #         #     "creation_time": "2011-12-02T14:56:33.000000Z"
        #         # }
        #         self.tags = None

        PROGRAM_COUNT   = {'src': [['ff', 'nb_programs']]}
        STREAM_COUNT    = {'src': [['ff', 'nb_streams']]}
        FORMAT_NAME     = {'src': [['ff', 'format_name']]}
        START_TIME      = {'src': [['ff', 'start_time']]}
        DURATION        = {'src': [['ff', 'duration']]}
        SIZE            = {'src': [['ff', 'size']]}
        TAGS            = {'src': [['ff', 'tags']]}

        FORMAT              = {'src': [['mi', 'Format']]}
        FORMAT_COMMERCIAL   = {'src': [['mi', 'Format_Commercial']]}
        FORMAT_SETTINGS     = {'src': [['mi', 'Format_Settings']]}
        FORMAT_VERSION      = {'src': [['mi', 'Format_Version']]}
        FORMAT_PROFILE      = {'src': [['mi', 'Format_Profile']]}
        ENCODED_DATE        = {'src': [['mi', 'Encoded_Date']]}
        ENCODED_APPLICATION_COMPANYNAME = {'src': [['mi', 'Encoded_Application_CompanyName']]}
        ENCODED_APPLICATION_VERSION     = {'src': [['mi', 'Encoded_Application_Version']]}
        ENCODED_APPLICATION_NAME        = {'src': [['mi', 'Encoded_Application_Name']]}
        ENCODED_LIBRARY_VERSION         = {'src': [['mi', 'Encoded_Library_Version']]}
        ENCODED_LIBRARY_NAME            = {'src': [['mi', 'Encoded_Library_Name']]}

        def __init__(self):
            super().__init__()
            # self.miFormat = self.MiFormat()
            # self.ffFormat = self.FfFormat()
            self.program_count = None
            self.stream_count = None
            self.format_name = None
            self.start_time = None
            self.duration = None
            self.size = None
            self.tags = self.Tags()

            self.Format = None
            self.Format_Commercial = None
            self.Format_Settings = None
            self.Format_Version = None
            self.Format_Profile = None
            self.Encoded_Date = None
            self.Encoded_Application_CompanyName = None
            self.Encoded_Application_Version = None
            self.Encoded_Application_Name = None
            self.Encoded_Library_Version = None
            self.Encoded_Library_Name = None

    class VideoTrack(JSONer):
        DURATION_MS = {'src': [['mi', 'Duration']]}
        DURATION = {'src': [['ff', 'duration']]}

        INDEX           = {'src': [['ff', 'index']]}
        INDEX_KIND      = {'src': [['mi', 'StreamKindID']]}
        CODEC           = {'src': [['ff', 'codec_name']]}
        WIDTH           = {'src': [['mi', 'Stored_Width'], ['ff', 'width'], ['mi', 'Sampled_Width'], ['mi', 'Width']]}
        HEIGHT          = {'src': [['mi', 'Stored_Height'], ['ff', 'height'], ['mi', 'Sampled_Height'], ['mi', 'Height']]}
        HEIGHT_ORIGINAL = {'src': [['mi', 'Height_Original']]}
        HEIGHT_OFFSET   = {'src': [['mi', 'Height_Offset']]}
        DAR             = {'src': [['ff', 'display_aspect_ratio']]}
        # DURATION        = {'src': [['ff', 'duration']]}
        # 'PixelAspectRatio': 1.0,
        # 'PixelAspectRatio_Original': 1.126,
        # 'sample_aspect_ratio': '152:135'
        # PAR = {'src': } PAR
        PIX_FMT         = {'src': [['ff', 'pix_fmt']]}
        COLOR_RANGE     = {'src': [['ff', 'color_range']]}
        COLOR_PRIMARIES = {'src': [['ff', 'color_primaries']]}
        PROGRESSIVE     = {'src': [['mi', 'ScanType']], 'map': {'Progressive': True, 'Interlaced': False}}
        FIELD_ORDER     = {'src': [['mi', 'ScanOrder']], 'def': 'PFF'}
        FPS             = {'src': [['ff', 'r_frame_rate']]}
        FPS_AVG         = {'src': [['ff', 'avg_frame_rate']]}
        TIME_BASE       = {'src': [['ff', 'time_base']]}
        START_TIME      = {'src': [['ff', 'start_time']]}
        DELAY           = {'src': [['mi', 'Delay']]}
        DISPOSITION     = {'src': [['ff', 'disposition']]}
        TAGS            = {'src': [['ff', 'tags']]}

        class Tags(JSONer):
            def __init__(self):
                super().__init__()
                self.language = None
                self.title = None

        class Disposition(JSONer):
            def __init__(self):
                super().__init__()
                #     "default": 1,
                #     "dub": 0,
                #     "original": 0,
                #     "comment": 0,
                #     "lyrics": 0,
                #     "karaoke": 0,
                #     "forced": 0,
                #     "hearing_impaired": 0,
                #     "visual_impaired": 0,
                #     "clean_effects": 0,
                #     "attached_pic": 0,
                #     "timed_thumbnails": 0

        # Type helpers

        class Dar(Rational):
            def __init__(self, *args):
                super().__init__(*args)

        class Par(Rational):
            def __init__(self, *args):
                super().__init__(*args)

        class Fps(Rational):
            def __init__(self, *args):
                super().__init__(*args)

        class Fps_avg(Rational):
            def __init__(self, *args):
                super().__init__(*args)

        class Time_base(Rational):
            def __init__(self, *args):
                super().__init__(*args)

        class Slice(JSONer):
            class Timebase(Rational):
                def __init__(self, *args):
                    super().__init__(*args)

            def __init__(self, setup=None):
                super().__init__()
                self.length = 0
                self.pattern_offset = 0
                self.time = 0
                self.crc = []
                self.size = 0
                self.timebase: self.Timebase = self.Timebase()
                self.pts = 0
                self.pts_time = 0.0
                if setup:
                    self.update_json(setup)

            def embed(self):
                return 'pattern_offset={};length={};crc={}'.format(self.pattern_offset, self.length, ','.join([str(_) for _ in self.crc]))

        class Segment(JSONer):
            def __init__(self):
                super().__init__()
                self.size = 0
                self.path = None

        def __init__(self):
            super().__init__()
            # Auto-captured info
            # MediaInfo track duration
            self.Duration_ms = None
            # FFMpeg track duration
            self.duration = None
            self.index = None
            self.index_kind = None
            self.codec = None
            self.width = None
            self.height = None
            self.height_original = 0
            self.height_offset = 0
            self.dar: self.Dar = self.Dar(16, 9)
            # Pixel aspect ratio is being calculated from DAR, width and height_original in "combine_ffprobe_mediainfo_track" function
            self.par: self.Par = self.Par(1, 1)
            self.pix_fmt = None
            self.color_range = None
            self.color_primaries = None
            self.progressive = True
            self.field_order = 'PFF'
            self.fps: self.Fps = self.Fps(25, 1)
            self.fps_avg: self.Fps_avg = self.Fps_avg(25, 1)
            self.time_base: self.Time_base = None #self.Time_base(1, 1)
            self.start_time = 0.0
            self.delay = 0
            self.disposition = self.Disposition()
            self.tags = self.Tags()

            # ID(s) of reference video(s): separate video file for every component
            # single ID in case of mono input, two IDs for stereo, etc.
            self.previews: List[str] = []
            # ID of mediafile that consists of archived video track
            self.archive = None

            self.slices: List[self.Slice] = []
            self.segments: List[self.Segment] = []

        @staticmethod
        def fit_video(src, dst, dw: int, dh: int, round_w=3, round_h=2):
            """
            Fit video into given display size, rounding dimensions to 2^round_*
            :param src: source VideoTrack object
            :param dst: target VideoTrack object
            :param dw: display width
            :param dh: display height
            :param round_w: horizontal round value
            :param round_h: vertical round value
            :return:
            """

            # src, dst:
            # dw, dh: display boundaries
            sr2pw = pow(2, round_w)
            sr2ph = pow(2, round_h)
            ssw = src.par.val() * src.width
            kw = dw / ssw
            kh = dh / src.height
            display_width = dw
            display_height = dh
            if abs(kw - kh) > 0.00001:
                maskw = 0x10000 - sr2pw
                maskh = 0x10000 - sr2ph
                if kw < kh:
                    display_height = maskh & (min(int(kw * src.height), dh) + (sr2pw >> 1))
                else:
                    display_width = maskw & (min(int(kh * ssw), dw)  + (sr2ph >> 1))
            dst.width = display_width
            dst.height = display_height

        def ref_add(self, w=640, h=360):
            # Create preview mediafile for this stream
            mf: MediaFile = MediaFile()
            mf.role = MediaFile.Role.PREVIEW
            self.previews.append(mf.guid)
            vt = MediaFile.VideoTrack()
            MediaFile.VideoTrack.fit_video(self, vt, w, h)
            mf.videoTracks.append(vt)
            return mf

    class AudioTrack(JSONer):
        class Tags(JSONer):
            def __init__(self):
                super().__init__()
                self.language = None
                self.track_name = None

        class Disposition(JSONer):
            def __init__(self):
                super().__init__()
                self.default = None
                self.dub = None
                self.original = None
                self.comment = None
                self.lyrics = None
                self.karaoke = None
                self.forced = None
                self.hearing_impaired = None
                self.visual_impaired = None
                self.clean_effects = None
                self.attached_pic = None
                self.timed_thumbnails = None

        DURATION_MS      = {'src': [['mi', 'Duration']]}
        DURATION         = {'src': [['ff', 'duration']]}
        CHANNELPOSITIONS = {'src': [['mi', 'ChannelPositions']]}
        CHANNELLAYOUT    = {'src': [['mi', 'ChannelLayout']]}

        INDEX            = {'src': [['ff', 'index']]}
        INDEX_KIND       = {'src': [['mi', 'StreamKindID']]}
        CODEC            = {'src': [['ff', 'codec_name']]}
        SAMPLE_FMT       = {'src': [['ff', 'sample_fmt']]}
        SAMPLE_RATE      = {'src': [['ff', 'sample_rate']]}
        CHANNELS         = {'src': [['ff', 'channels']]}
        CHANNEL_LAYOUT   = {'src': [['ff', 'channel_layout']]}
        BITS_PER_SAMPLE  = {'src': [['ff', 'bits_per_sample']]}
        START_TIME       = {'src': [['ff', 'start_time']]}
        DISPOSITION      = {'src': [['ff', 'disposition']]}
        TAGS             = {'src': [['ff', 'tags']]}

        def __init__(self):
            super().__init__()
            # self.Codec = None
            # MediaInfo track duration
            self.Duration_ms = None
            # FFMpeg track duration
            self.duration = None
            # self.BitRate = None
            self.ChannelPositions = None
            # self.Channels = None
            self.ChannelLayout = None
            # self.SamplingRate = None
            # self.BitDepth = None

            self.index = None
            self.index_kind = None
            self.codec = None
            self.sample_fmt = None
            self.sample_rate = None
            self.channels = None
            self.channel_layout = None
            self.bits_per_sample = 0
            self.start_time = 0.0
            self.disposition = self.Disposition()
            self.tags = self.Tags()

            # ID(s) of reference audio(s): separate audio file for every channel
            # single ID in case of mono input, two IDs for stereo, 6 IDs for 5.1, etc.
            self.previews: List[str] = []
            # ID of mediafile that consists of extracted audio track
            self.extract = None

            # self.audioResults = None

    class SubTrack(JSONer):
        class Tags(JSONer):
            def __init__(self):
                super().__init__()
                self.language = None

        DURATION_MS = {'src': [['mi', 'Duration']]}
        DURATION = {'src': [['ff', 'duration']]}

        INDEX = {'src': [['ff', 'index']]}
        INDEX_KIND = {'src': [['mi', 'StreamKindID']]}
        CODEC = {'src': [['ff', 'codec_name']]}
        START_TIME = {'src': [['ff', 'start_time']]}
        # DISPOSITION = {'src': [['ff', 'disposition']]}
        TAGS = {'src': [['ff', 'tags']]}

        def __init__(self):
            super().__init__()
            # MediaInfo track duration
            self.Duration_ms = None
            # FFMpeg track duration
            self.duration = None

            self.index = None
            self.index_kind = None
            self.codec = None
            self.start_time = 0.0
            # self.disposition = self.Disposition()
            self.tags = self.Tags()

            # ID(s) of reference subtitles track(s)
            self.previews: List[str] = []
            # ID of mediafile that consists of extracted subtitles track
            self.extract = None

    class Role:
        ORIGINAL = 0
        TRANSIT = 1
        PREVIEW = 2

    # Support classes

    class Master(Guid):
        def __init__(self, v=None):
            super().__init__(v)

    class Asset(Guid):
        def __init__(self):
            super().__init__()

    def __init__(self, name='', guid=0):
        super().__init__(name=name, guid=guid)
        # This flag is set when media file is created as reference of media component (video or audio channel)
        self.role = self.Role.PREVIEW
        #self.role = MediaFile.Role.ORIGINAL
        # Master mediafile: guid of source media
        self.master = self.Master()
        # Set of ASSETs that use this mediafile
        self.assets: List[self.Asset] = []
        self.source = self.Source()
        self.format = self.Format()
        self.videoTracks: List[self.VideoTrack] = []
        self.audioTracks: List[self.AudioTrack] = []
        self.subTracks: List[self.SubTrack] = []

    def update_json(self, mf):
        # Specialized 'update_json' procedure for correct tracks merging

        if 'guid' in mf:
            self.guid.set(mf['guid'])
        if 'name' in mf:
            self.name = mf['name']
        if 'ctime' in mf:
            self.ctime = str(mf['ctime'])
        if 'mtime' in mf:
            self.mtime = str(mf['mtime'])

        if 'role' in mf:
            self.role = mf['role']
        if 'master' in mf:
            self.master = mf['master']
        if 'assets' in mf and type(mf['assets']) is list:
            self.assets = [_ for _ in mf['assets']]
        if 'source' in mf:
            self.source.update_json(mf['source'])
        if 'format' in mf:
            self.format.update_json(mf['format'])
        if 'videoTracks' in mf and mf['videoTracks'] is not None:
            for i, t in enumerate(mf['videoTracks']):
                if len(self.videoTracks) == i:
                    self.videoTracks.append(MediaFile.VideoTrack())
                self.videoTracks[i].update_json(t)
        if 'audioTracks' in mf and mf['audioTracks'] is not None:
            for i, t in enumerate(mf['audioTracks']):
                if len(self.audioTracks) == i:
                    self.audioTracks.append(MediaFile.AudioTrack())
                self.audioTracks[i].update_json(t)
        if 'subTracks' in mf and mf['subTracks'] is not None:
            for i, t in enumerate(mf['subTracks']):
                if len(self.subTracks) == i:
                    self.subTracks.append(MediaFile.SubTrack())
                self.subTracks[i].update_json(t)

    TABLE_SETUP = {
        "relname": "trix_files",
        "fields": [
            ["role", "integer NOT NULL"],
            ["master", "uuid"],
            ["assets", "uuid[]"],
            ["source", "json NOT NULL"],
            ["format", "json"],
            ["videoTracks", "json[]"],
            ["audioTracks", "json[]"],
            ["subTracks", "json[]"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }
