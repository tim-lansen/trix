# This script was automatically generated by 'class_py2coffee' from Python class MediaFile
# 2017-10-26 08:27:05

class MediaFile_SubTrack_Tags
    constructor: () ->
        @unmentioned = {}
        @language = null  # None


class MediaFile_SubTrack
    constructor: () ->
        @unmentioned = {}
        @Duration_ms = null  # None
        @duration = null  # None
        @index = null  # None
        @index_kind = null  # None
        @codec = null  # None
        @start_time = null  # 0.0
        @tags = {}
        @previews = []
        @extract = null  # None


class MediaFile_AudioTrack_Tags
    constructor: () ->
        @unmentioned = {}
        @language = null  # None
        @track_name = null  # None


class MediaFile_AudioTrack_Disposition
    constructor: () ->
        @unmentioned = {}
        @["default"] = null  # None
        @dub = null  # None
        @original = null  # None
        @comment = null  # None
        @lyrics = null  # None
        @karaoke = null  # None
        @forced = null  # None
        @hearing_impaired = null  # None
        @visual_impaired = null  # None
        @clean_effects = null  # None
        @attached_pic = null  # None
        @timed_thumbnails = null  # None


class MediaFile_AudioTrack
    constructor: () ->
        @unmentioned = {}
        @Duration_ms = null  # None
        @duration = null  # None
        @ChannelPositions = null  # None
        @ChannelLayout = null  # None
        @index = null  # None
        @index_kind = null  # None
        @codec = null  # None
        @sample_fmt = null  # None
        @sample_rate = null  # None
        @channels = null  # None
        @channel_layout = null  # None
        @bits_per_sample = 0
        @start_time = null  # 0.0
        @disposition = {}
        @tags = {}
        @previews = []
        @extract = null  # None


class MediaFile_VideoTrack_Tags
    constructor: () ->
        @unmentioned = {}
        @language = null  # None
        @title = null  # None


class MediaFile_VideoTrack_Disposition
    constructor: () ->
        @unmentioned = {}


class MediaFile_VideoTrack
    constructor: () ->
        @unmentioned = {}
        @Duration_ms = null  # None
        @duration = null  # None
        @index = null  # None
        @index_kind = null  # None
        @codec = null  # None
        @width = null  # None
        @height = null  # None
        @height_original = 0
        @height_offset = 0
        @dar = "16:9"
        @par = "1:1"
        @pix_fmt = null  # None
        @color_range = null  # None
        @color_primaries = null  # None
        @progressive = null  # True
        @field_order = "PFF"
        @fps = "25:1"
        @fps_avg = "25:1"
        @start_time = null  # 0.0
        @delay = 0
        @disposition = {}
        @tags = {}
        @previews = []
        @extract = null  # None


class MediaFile_Format_Tags
    constructor: () ->
        @unmentioned = {}
        @encoder = null  # None
        @creation_time = null  # None


class MediaFile_Format
    constructor: () ->
        @unmentioned = {}
        @program_count = null  # None
        @stream_count = null  # None
        @format_name = null  # None
        @start_time = null  # None
        @duration = null  # None
        @size = null  # None
        @tags = {}
        @Format = null  # None
        @Format_Commercial = null  # None
        @Format_Settings = null  # None
        @Format_Version = null  # None
        @Format_Profile = null  # None
        @Encoded_Date = null  # None
        @Encoded_Application_CompanyName = null  # None
        @Encoded_Application_Version = null  # None
        @Encoded_Application_Name = null  # None
        @Encoded_Library_Version = null  # None
        @Encoded_Library_Name = null  # None


class MediaFile_Source
    constructor: () ->
        @unmentioned = {}
        @path = null  # None
        @url = null  # None
        @chunks = null  # None


class MediaFile
    constructor: () ->
        @unmentioned = {}
        @guid = "04461768-9bec-44de-b3db-9375f2fe16e2"
        @name = ""
        @ctime = null  # None
        @mtime = null  # None
        @role = 0
        @master = "00000000-0000-0000-0000-000000000000"
        @assets = []
        @source = {}
        @format = {}
        @videoTracks = []
        @audioTracks = []
        @subTracks = []
