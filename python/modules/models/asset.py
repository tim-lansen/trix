# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

from typing import List

from modules.models.record import *


class Asset(Record):
    class MediaFile(JSONer):
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
            #         self.Duration = None
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

            PROGRAM_COUNT = {'src': [['ff', 'nb_programs']]}
            STREAM_COUNT = {'src': [['ff', 'nb_streams']]}
            FORMAT_NAME = {'src': [['ff', 'format_name']]}
            START_TIME = {'src': [['ff', 'start_time']]}
            DURATION = {'src': [['ff', 'duration']]}
            SIZE = {'src': [['ff', 'size']]}
            TAGS = {'src': [['ff', 'tags']]}

            FORMAT = {'src': [['mi', 'Format']]}
            FORMAT_COMMERCIAL = {'src': [['mi', 'Format_Commercial']]}
            FORMAT_SETTINGS = {'src': [['mi', 'Format_Settings']]}
            FORMAT_VERSION = {'src': [['mi', 'Format_Version']]}
            FORMAT_PROFILE = {'src': [['mi', 'Format_Profile']]}
            ENCODED_DATE = {'src': [['mi', 'Encoded_Date']]}
            ENCODED_APPLICATION_COMPANYNAME = {'src': [['mi', 'Encoded_Application_CompanyName']]}
            ENCODED_APPLICATION_VERSION = {'src': [['mi', 'Encoded_Application_Version']]}
            ENCODED_APPLICATION_NAME = {'src': [['mi', 'Encoded_Application_Name']]}
            ENCODED_LIBRARY_VERSION = {'src': [['mi', 'Encoded_Library_Version']]}
            ENCODED_LIBRARY_NAME = {'src': [['mi', 'Encoded_Library_Name']]}

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
            INDEX  = {'src': [['ff', 'index']]}
            CODEC  = {'src': [['ff', 'codec_name']]}
            WIDTH  = {'src': [['mi', 'Stored_Width'], ['ff', 'width'], ['mi', 'Sampled_Width'], ['mi', 'Width']]}
            HEIGHT = {'src': [['mi', 'Stored_Height'], ['ff', 'height'], ['mi', 'Sampled_Height'], ['mi', 'Height']]}
            HEIGHT_ORIGINAL = {'src': [['mi', 'Height_Original']]}
            HEIGHT_OFFSET   = {'src': [['mi', 'Height_Offset']]}
            DAR             = {'src': [['ff', 'display_aspect_ratio']]}
            # 'PixelAspectRatio': 1.0,
            # 'PixelAspectRatio_Original': 1.126,
            # 'sample_aspect_ratio': '152:135'
            # PAR = {'src': } TODO: ignore or what???
            PIX_FMT         = {'src': [['ff', 'pix_fmt']]}
            COLOR_RANGE     = {'src': [['ff', 'color_range']]}
            COLOR_PRIMARIES = {'src': [['ff', 'color_primaries']]}
            PROGRESSIVE     = {'src': [['mi', 'ScanType']], 'map': {'Progressive': True, 'Interlaced': False}}
            FIELD_ORDER     = {'src': [['mi', 'ScanOrder']], 'def': 'PFF'}
            FPS             = {'src': [['ff', 'r_frame_rate']]}
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

            def __init__(self):
                super().__init__()
                self.index = None
                self.codec = None
                self.width = None
                self.height = None
                self.height_original = 0
                self.height_offset = 0
                self.dar = None
                # self.par = '1/1'
                self.pix_fmt = None
                self.color_range = None
                self.color_primaries = None
                self.progressive = True
                self.field_order = 'PFF'
                self.fps = None
                self.start_time = 0.0
                self.delay = 0
                self.disposition = self.Disposition()
                self.tags = self.Tags()

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

            INDEX = {'src': [['ff', 'index']]}
            CODEC = {'src': [['ff', 'codec_name']]}
            DISPOSITION = {'src': [['ff', 'disposition']]}
            TAGS = {'src': [['ff', 'tags']]}

            def __init__(self):
                super().__init__()
                # self.Codec = None
                # self.Duration = None
                # self.BitRate = None
                # self.Channels = None
                # self.ChannelLayout = None
                # self.SamplingRate = None
                # self.BitDepth = None

                self.index = None
                self.codec = None
                self.sample_fmt = None
                self.sample_rate = None
                self.channels = None
                self.channel_layout = None
                self.bits_per_sample = 0
                self.disposition = self.Disposition()
                self.tags = self.Tags()

        class SubTrack(JSONer):
            class MiSubTrack(JSONer):
                def __init__(self):
                    super().__init__()

            class FfSubTrack(JSONer):
                def __init__(self):
                    super().__init__()

            def __init__(self):
                super().__init__()
                self.miSubTrack = self.MiSubTrack()
                self.ffSubTrack = self.FfSubTrack()

        def __init__(self):
            super().__init__()
            self.url = None
            self.format = self.Format()
            self.videoTracks: List[self.VideoTrack] = []
            self.audioTracks: List[self.AudioTrack] = []
            self.subTracks: List[self.SubTrack] = []

    def __init__(self):
        super().__init__()
        self.mediaFiles: List[self.MediaFile] = []


