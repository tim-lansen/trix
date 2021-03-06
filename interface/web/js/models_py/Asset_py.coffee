# This script was automatically generated by 'class_py2coffee' from Python class Asset
# 2017-11-16 09:18:33

class Asset_SubStream_Sync
    constructor: () ->
        @offset1 = null  # None
        @offset2 = null  # None
        @delay1 = null  # None
        @delay2 = null  # None


class Asset_SubStream
    constructor: () ->
        @type = null  # None
        @layout = null  # None
        @channels = []
        @language = null  # None
        @program_in = null  # None
        @program_out = null  # None
        @sync = {}
        @collector = "00000000-0000-0000-0000-000000000000"


class Asset_AudioStream_Sync
    constructor: () ->
        @offset1 = null  # None
        @offset2 = null  # None
        @delay1 = null  # None
        @delay2 = null  # None


class Asset_AudioStream
    constructor: () ->
        @type = null  # None
        @layout = null  # None
        @channels = []
        @language = null  # None
        @program_in = null  # None
        @program_out = null  # None
        @sync = {}
        @collector = "00000000-0000-0000-0000-000000000000"


class Asset_VideoStream_Cropdetect
    constructor: () ->
        @w = null  # None
        @h = null  # None
        @x = null  # None
        @y = null  # None
        @sar = null  # None
        @aspect = null  # None


class Asset_VideoStream_Sync
    constructor: () ->
        @offset1 = null  # None
        @offset2 = null  # None
        @delay1 = null  # None
        @delay2 = null  # None


class Asset_VideoStream
    constructor: () ->
        @type = null  # None
        @layout = null  # None
        @channels = []
        @language = null  # None
        @program_in = null  # None
        @program_out = null  # None
        @sync = {}
        @collector = "00000000-0000-0000-0000-000000000000"
        @cropdetect = {}
        @fpsOriginal = "1:1"
        @fpsEncode = "1:1"


class Asset
    constructor: () ->
        @guid = "00000000-0000-0000-0000-000000000000"
        @name = null  # None
        @ctime = null  # None
        @mtime = null  # None
        @mediaFiles = []
        @mediaFilesExtra = []
        @videoStreams = []
        @audioStreams = []
        @subStreams = []
        @taskId = "00000000-0000-0000-0000-000000000000"
        @proxyId = "00000000-0000-0000-0000-000000000000"
        @programId = "00000000-0000-0000-0000-000000000000"
        @programName = ""
