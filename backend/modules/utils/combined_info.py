# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import re
import os
import sys
import uuid
import json
import traceback
from pprint import pprint
from subprocess import Popen, PIPE

from modules.models.mediafile import MediaFile
from .jsoner import JSONer
from .types import Guid, Rational, guess_type
from .log_console import Logger, tracer


#TODO get frame side data
# 'ffprobe -print_format json -v quiet -show_frames -show_entries frame=side_data -select_streams v:0 -read_intervals %+00:00:00.01'


def get_ffprobe_info(filename, refine_duration=True):

    # def get_real_duration(src, codec_type, idx, format_duration):
    #     legacy_symbols = re.compile(r'[^a-zA-Z\d\.\-_:\[\]]')
    #     extract_braces = re.compile(r'\[.+?\]')
    #     replace_spaces = re.compile(r'(\s)+')
    #     #print 'Get real duration for {0}:{1}'.format(src, codec_type)
    #     if codec_type == 'video':
    #         params = ['-vf', 'showinfo', '-vcodec', 'rawvideo']
    #     elif codec_type == 'audio':
    #         params = ['-af', 'ashowinfo', '-acodec', 'pcm_s16le']
    #     else:
    #         return None
    #     pts_time_first = None
    #     proc = Popen(
    #         [FFMPEG, '-y', '-i', src, '-t', '60', '-map', '0:{0}'.format(idx)]
    #         + params
    #         + ['-f', 'null', 'nul'],
    #         stderr=PIPE, stdin=PIPE)
    #     while proc.poll() is None:
    #         cap = proc.stderr.readline()
    #         if pts_time_first is None and 'pts_time:' in cap:
    #             try:
    #                 pts_time_first = float(cap.split('pts_time:', 1)[1].split(' ', 1)[0])
    #                 proc.stdin.write('q')
    #             except:
    #                 pass
    #     if pts_time_first is None:
    #         print 'Cannot get first PTS from stream'
    #         return None
    #     pts_time_last = None
    #     while pts_time_last is None and format_duration > 5.0:
    #         format_duration -= 5.0
    #         proc = Popen(
    #             [FFMPEG, '-nostats', '-y', '-ss', str(format_duration), '-i', src, '-map', '0:{0}'.format(idx)]
    #             + params + ['-f', 'null', 'nul'],
    #             stderr=PIPE, stdin=PIPE)
    #         while proc.poll() is None:
    #             cap = proc.stderr.readline()
    #             if 'pts_time:' in cap:
    #                 try:
    #                     pts_time_last = format_duration + float(cap.split('pts_time:', 1)[1].split(' ', 1)[0])
    #                 except:
    #                     pass
    #     if pts_time_last is None:
    #         print 'Cannot get last PTS from stream'
    #         return None
    #     return {'pts_time_first': pts_time_first, 'pts_time_last': pts_time_last, 'duration': pts_time_last - pts_time_first}

    proc = Popen('ffprobe -print_format json -v quiet -show_streams -show_format {}'.format(filename).split(' '), stderr=PIPE, stdout=PIPE)
    output, error = proc.communicate()
    # proc = Popen('ffprobe -print_format json -v quiet -show_frames -show_entries frame=side_data -select_streams v:0 -read_intervals %+00:00:00.01'.format(filename).split(' '), stderr=PIPE, stdout=PIPE)
    # output, error = proc.communicate()
    return output.decode()


def get_media_info(filename):
    proc_data = ['mediainfo', '--Language=raw', '--Full', filename]
    proc = Popen(proc_data, stdout=PIPE, stderr=PIPE)
    output, error = proc.communicate()
    return output.decode()


def object_hook(obj):
    for k in obj:
        v = obj[k]
        if isinstance(v, str):
            obj[k] = guess_type(v)
    return obj


# Example MediaInfo output
#
# General
# Count                            : 325
# StreamCount                      : 1
# StreamKind                       : General
# StreamKind/String                : General
# StreamKindID                     : 0
# UniqueID                         : 184990659868305317247132685773812810764
# UniqueID/String                  : 184990659868305317247132685773812810764 (0x8B2BE7B66B159612B9D1A62B7D78440C)
# VideoCount                       : 1
# AudioCount                       : 2
# TextCount                        : 3
# Video_Format_List                : AVC
# Video_Format_WithHint_List       : AVC
# Video_Codec_List                 : AVC
# Video_Language_List              : en
# Audio_Format_List                : AAC / AC-3
# Audio_Format_WithHint_List       : AAC / AC-3
# Audio_Codec_List                 : AAC LC / AC3
# Audio_Language_List              : ru / en
# Text_Format_List                 : UTF-8 / UTF-8 / UTF-8
# Text_Format_WithHint_List        : UTF-8 / UTF-8 / UTF-8
# Text_Codec_List                  : UTF-8 / UTF-8 / UTF-8
# Text_Language_List               : ru / ru / en
# CompleteName                     : F:\Kinozal\the.pixar.story.bluray.720p.x264.RUS.mkv
# FolderName                       : F:\Kinozal
# FileName                         : the.pixar.story.bluray.720p.x264.RUS
# FileExtension                    : mkv
# Format                           : Matroska
# Format/String                    : Matroska
# Format/Url                       : http://packs.matroska.org/
# Format/Extensions                : mkv mk3d mka mks
# Format_Commercial                : Matroska
# Format_Version                   : Version 2
# Codec                            : Matroska
# Codec/String                     : Matroska
# Codec/Url                        : http://packs.matroska.org/
# Codec/Extensions                 : mkv mk3d mka mks
# FileSize                         : 1814335252
# FileSize/String                  : 1.69 GiB
# FileSize/String1                 : 2 GiB
# FileSize/String2                 : 1.7 GiB
# FileSize/String3                 : 1.69 GiB
# FileSize/String4                 : 1.690 GiB
# Duration                         : 5318869
# Duration/String                  : 1h 28mn
# Duration/String1                 : 1h 28mn 38s 869ms
# Duration/String2                 : 1h 28mn
# Duration/String3                 : 01:28:38.869
# Duration/String4                 : 01:28:40;05
# Duration/String5                 : 01:28:38.869 (01:28:40;05)
# OverallBitRate                   : 2728904
# OverallBitRate/String            : 2729 Kbps
# FrameRate                        : 23.976
# FrameRate/String                 : 23.976 fps2
# FrameCount                       : 127525
# Encoded_Date                     : UTC 2011-12-02 14:56:33
# File_Created_Date                : UTC 2016-01-22 19:33:00.750
# File_Created_Date_Local          : 2016-01-22 22:33:00.750
# File_Modified_Date               : UTC 2016-01-22 20:18:46.314
# File_Modified_Date_Local         : 2016-01-22 23:18:46.314
# Encoded_Application              : mkvmerge v4.9.1 ('Ich will') сборка от Jul 11 2011 23:53:15
# Encoded_Application/String       : mkvmerge v4.9.1 ('Ich will') сборка от Jul 11 2011 23:53:15
# Encoded_Library                  : libebml v1.2.1 + libmatroska v1.1.1
# Encoded_Library/String           : libebml v1.2.1 + libmatroska v1.1.1
#
# Video
# Count                            : 338
# StreamCount                      : 1
# StreamKind                       : Video
# StreamKind/String                : Video
# StreamKindID                     : 0
# StreamOrder                      : 0
# ID                               : 1
# ID/String                        : 1
# UniqueID                         : 2444284084
# Format                           : AVC
# Format/Info                      : Advanced Video Codec
# Format/Url                       : http://developers.videolan.org/x264.html
# Format_Commercial                : AVC
# Format_Profile                   : High@L5.1
# Format_Settings                  : CABAC / 3 Ref Frames
# Format_Settings_CABAC            : Yes
# Format_Settings_CABAC/String     : Yes
# Format_Settings_RefFrames        : 3
# Format_Settings_RefFrames/String : 3 frame2
# Format_Settings_GOP              : N=1
# InternetMediaType                : video/H264
# CodecID                          : V_MPEG4/ISO/AVC
# CodecID/Url                      : http://ffdshow-tryout.sourceforge.net/
# Codec                            : V_MPEG4/ISO/AVC
# Codec/String                     : AVC
# Codec/Family                     : AVC
# Codec/Info                       : Advanced Video Codec
# Codec/Url                        : http://ffdshow-tryout.sourceforge.net/
# Codec_Profile                    : High@L5.1
# Codec_Settings                   : CABAC / 3 Ref Frames
# Codec_Settings_CABAC             : Yes
# Codec_Settings_RefFrames         : 3
# Duration                         : 5318861
# Duration/String                  : 1h 28mn
# Duration/String1                 : 1h 28mn 38s 861ms
# Duration/String2                 : 1h 28mn
# Duration/String3                 : 01:28:38.861
# Duration/String4                 : 01:28:40;05
# Duration/String5                 : 01:28:38.861 (01:28:40;05)
# Width                            : 1280
# Width/String                     : 1280 pixel3
# Height                           : 720
# Height/String                    : 720 pixel3
# Sampled_Width                    : 1280
# Sampled_Height                   : 720

# Height_Offset                    : 32             == optional
# Height_Offset/String             : 32 pixel2
# Height_Original                  : 608
# Height_Original/String           : 608 pixel3
# Sampled_Width                    : 720
# Sampled_Height                   : 608

# PixelAspectRatio                 : 1.000
# DisplayAspectRatio               : 1.778
# DisplayAspectRatio/String        : 16:9
# FrameRate_Mode                   : CFR
# FrameRate_Mode/String            : CFR
# FrameRate                        : 23.976
# FrameRate/String                 : 23.976 (24000/1001) fps2
# FrameRate_Num                    : 24000
# FrameRate_Den                    : 1001
# FrameCount                       : 127525
# Resolution                       : 8
# Resolution/String                : 8 bit3
# Colorimetry                      : 4:2:0
# ColorSpace                       : YUV
# ChromaSubsampling                : 4:2:0
# ChromaSubsampling/String         : 4:2:0
# BitDepth                         : 8
# BitDepth/String                  : 8 bit3
# ScanType                         : Progressive
# ScanType/String                  : Progressive
# Interlacement                    : PPF
# Interlacement/String             : Interlaced_PPF
# Delay                            : 0
# Delay/String3                    : 00:00:00.000
# Delay_Source                     : Container
# Delay_Source/String              : Container
# Encoded_Library                  : x264 - core 60 r900 a9af942
# Encoded_Library/String           : x264 core 60 r900 a9af942
# Encoded_Library_Name             : x264
# Encoded_Library_Version          : core 60 r900 a9af942
# Encoded_Library_Settings         : cabac=1 / ref=3 / deblock=1:-2:-1 / analyse=0x3:0x113 / me=umh / subme=6 / brdo=0 / mixed_ref=0 / me_range=12 / chroma_me=1 / trellis=1 / 8x8dct=1 / cqm=0 / deadzone=21,11 / chroma_qp_offset=0 / threads=3 / nr=0 / decimate=1 / mbaff=0 / bframes=16 / b_pyramid=1 / b_adapt=1 / b_bias=0 / direct=3 / wpredb=1 / bime=0 / keyint=250 / keyint_min=25 / scenecut=40(pre) / rc=crf / crf=22.0 / rceq='blurCplx^(1-qComp)' / qcomp=1.00 / qpmin=10 / qpmax=51 / qpstep=4 / ip_ratio=1.40 / pb_ratio=1.30 / aq=2:1.00
# Default                          : Yes
# Default/String                   : Yes
# Forced                           : No
# Forced/String                    : No
#
# Audio #1
# Count                            : 275
# StreamCount                      : 2
# StreamKind                       : Audio
# StreamKind/String                : Audio
# StreamKindID                     : 0
# StreamKindPos                    : 1
# StreamOrder                      : 1
# ID                               : 2
# ID/String                        : 2
# UniqueID                         : 1027823022
# Format                           : AAC
# Format/Info                      : Advanced Audio Codec
# Format_Commercial                : AAC
# Format_Profile                   : LC
# CodecID                          : A_AAC
# Codec                            : AAC LC
# Codec/String                     : AAC LC
# Codec/Family                     : AAC
# Duration                         : 5318869
# Duration/String                  : 1h 28mn
# Duration/String1                 : 1h 28mn 38s 869ms
# Duration/String2                 : 1h 28mn
# Duration/String3                 : 01:28:38.869
# Duration/String5                 : 01:28:38.869
# Channel(s)                       : 2
# Channel(s)/String                : 2 channel2
# ChannelPositions                 : Front: L R
# ChannelPositions/String2         : 2/0/0
# ChannelLayout                    : L R
# SamplesPerFrame                  : 1024
# SamplingRate                     : 48000
# SamplingRate/String              : 48.0 KHz
# SamplingCount                    : 255305712
# FrameRate                        : 46.875
# FrameRate/String                 : 46.875 fps3 (1024 spf)
# Compression_Mode                 : Lossy
# Compression_Mode/String          : Lossy
# Delay                            : 0
# Delay/String3                    : 00:00:00.000
# Delay_Source                     : Container
# Delay_Source/String              : Container
# Video_Delay                      : 0
# Video_Delay/String3              : 00:00:00.000
# Video0_Delay                     : 0
# Video0_Delay/String3             : 00:00:00.000
# Title                            : VO
# Language                         : ru
# Language/String                  : ru
# Language/String1                 : ru
# Language/String2                 : ru
# Language/String3                 : rus
# Language/String4                 : ru
# Default                          : Yes
# Default/String                   : Yes
# Forced                           : No
# Forced/String                    : No
#
# Audio #2
# Count                            : 298
# StreamCount                      : 2
# StreamKind                       : Audio
# StreamKind/String                : Audio
# StreamKindID                     : 1
# StreamKindPos                    : 2
# StreamOrder                      : 2
# ID                               : 3
# ID/String                        : 3
# UniqueID                         : 1501014699
# Format                           : AC-3
# Format/Info                      : Audio Coding 3
# Format_Commercial                : AC-3
# Format_Settings_Mode             : Dolby Digital
# Format_Settings_Endianness       : Big
# CodecID                          : A_AC3
# Codec                            : AC3
# Codec/String                     : AC3
# Codec/Family                     : AC3
# Codec/Info                       : Dolby AC3
# Duration                         : 5318869
# Duration/String                  : 1h 28mn
# Duration/String1                 : 1h 28mn 38s 869ms
# Duration/String2                 : 1h 28mn
# Duration/String3                 : 01:28:38.869
# Duration/String5                 : 01:28:38.869
# BitRate_Mode                     : CBR
# BitRate_Mode/String              : CBR
# BitRate                          : 192000
# BitRate/String                   : 192 Kbps
# Channel(s)                       : 2
# Channel(s)/String                : 2 channel2
# ChannelPositions                 : Front: L R
# ChannelPositions/String2         : 2/0/0
# ChannelLayout                    : L R
# SamplesPerFrame                  : 1536
# SamplingRate                     : 48000
# SamplingRate/String              : 48.0 KHz
# SamplingCount                    : 255305712
# FrameRate                        : 31.250
# FrameRate/String                 : 31.250 fps3 (1536 spf)
# Resolution                       : 16
# Resolution/String                : 16 bit3
# BitDepth                         : 16
# BitDepth/String                  : 16 bit3
# Compression_Mode                 : Lossy
# Compression_Mode/String          : Lossy
# Delay                            : 0
# Delay/String3                    : 00:00:00.000
# Delay_Source                     : Container
# Delay_Source/String              : Container
# Video_Delay                      : 0
# Video_Delay/String3              : 00:00:00.000
# Video0_Delay                     : 0
# Video0_Delay/String3             : 00:00:00.000
# StreamSize                       : 127652856
# StreamSize/String                : 122 MiB (7%)
# StreamSize/String1               : 122 MiB
# StreamSize/String2               : 122 MiB
# StreamSize/String3               : 122 MiB
# StreamSize/String4               : 121.7 MiB
# StreamSize/String5               : 122 MiB (7%)
# StreamSize_Proportion            : 0.07036
# Language                         : en
# Language/String                  : en
# Language/String1                 : en
# Language/String2                 : en
# Language/String3                 : eng
# Language/String4                 : en
# ServiceKind                      : CM
# ServiceKind/String               : Complete Main
# Default                          : No
# Default/String                   : No
# Forced                           : No
# Forced/String                    : No
# bsid                             : 6
# dialnorm                         : -31
# dialnorm                         : -31 dB
# compr                            : -0.28
# compr                            : -0.28 dB
# dsurmod                          : 2
# dsurmod                          : Dolby Surround encoded
# acmod                            : 2
# lfeon                            : 0
# dialnorm_Average                 : -31
# dialnorm_Average                 : -31 dB
# dialnorm_Minimum                 : -31
# dialnorm_Minimum                 : -31 dB
# dialnorm_Maximum                 : -31
# dialnorm_Maximum                 : -31 dB
# dialnorm_Count                   : 1507
# compr_Average                    : -1.22
# compr_Average                    : -1.22 dB
# compr_Minimum                    : -4.08
# compr_Minimum                    : -4.08 dB
# compr_Maximum                    : 1.94
# compr_Maximum                    : 1.94 dB
# compr_Count                      : 402
#
# Text #1
# Count                            : 236
# StreamCount                      : 3
# StreamKind                       : Text
# StreamKind/String                : Text
# StreamKindID                     : 0
# StreamKindPos                    : 1
# StreamOrder                      : 3
# ID                               : 4
# ID/String                        : 4
# UniqueID                         : 1434369457
# Format                           : UTF-8
# Format_Commercial                : UTF-8
# CodecID                          : S_TEXT/UTF8
# CodecID/Info                     : UTF-8 Plain Text
# Codec                            : S_TEXT/UTF8
# Codec/String                     : UTF-8
# Codec/Info                       : UTF-8 Plain Text
# Title                            : license
# Language                         : ru
# Language/String                  : ru
# Language/String1                 : ru
# Language/String2                 : ru
# Language/String3                 : rus
# Language/String4                 : ru
# Default                          : No
# Default/String                   : No
# Forced                           : No
# Forced/String                    : No
#
# Text #2
# Count                            : 236
# StreamCount                      : 3
# StreamKind                       : Text
# StreamKind/String                : Text
# StreamKindID                     : 1
# StreamKindPos                    : 2
# StreamOrder                      : 4
# ID                               : 5
# ID/String                        : 5
# UniqueID                         : 1074135470
# Format                           : UTF-8
# Format_Commercial                : UTF-8
# CodecID                          : S_TEXT/UTF8
# CodecID/Info                     : UTF-8 Plain Text
# Codec                            : S_TEXT/UTF8
# Codec/String                     : UTF-8
# Codec/Info                       : UTF-8 Plain Text
# Title                            : notabenoid
# Language                         : ru
# Language/String                  : ru
# Language/String1                 : ru
# Language/String2                 : ru
# Language/String3                 : rus
# Language/String4                 : ru
# Default                          : No
# Default/String                   : No
# Forced                           : No
# Forced/String                    : No
#
# Text #3
# Count                            : 236
# StreamCount                      : 3
# StreamKind                       : Text
# StreamKind/String                : Text
# StreamKindID                     : 2
# StreamKindPos                    : 3
# StreamOrder                      : 5
# ID                               : 6
# ID/String                        : 6
# UniqueID                         : 3262886050
# Format                           : UTF-8
# Format_Commercial                : UTF-8
# CodecID                          : S_TEXT/UTF8
# CodecID/Info                     : UTF-8 Plain Text
# Codec                            : S_TEXT/UTF8
# Codec/String                     : UTF-8
# Codec/Info                       : UTF-8 Plain Text
# Language                         : en
# Language/String                  : en
# Language/String1                 : en
# Language/String2                 : en
# Language/String3                 : eng
# Language/String4                 : en
# Default                          : No
# Default/String                   : No
# Forced                           : No
# Forced/String                    : No

# MXF

# Other #1
# Count                            : 113
# StreamCount                      : 3
# StreamKind                       : Other
# StreamKind/String                : Other
# StreamKindID                     : 0
# StreamKindPos                    : 1
# ID                               : 0-Material
# ID/String                        : 0-Material
# Type                             : Time code
# Format                           : MXF TC
# Format_Commercial                : MXF TC
# TimeCode_FirstFrame              : 00:00:00:00
# TimeCode_Settings                : Material Package
# TimeCode_Striped                 : Yes
# TimeCode_Striped/String          : Yes
#
# Other #2
# Count                            : 113
# StreamCount                      : 3
# StreamKind                       : Other
# StreamKind/String                : Other
# StreamKindID                     : 1
# StreamKindPos                    : 2
# ID                               : 0-Source
# ID/String                        : 0-Source
# Type                             : Time code
# Format                           : MXF TC
# Format_Commercial                : MXF TC
# TimeCode_FirstFrame              : 00:00:00:00
# TimeCode_Settings                : Source Package
# TimeCode_Striped                 : Yes
# TimeCode_Striped/String          : Yes
#
# Other #3
# Count                            : 113
# StreamCount                      : 3
# StreamKind                       : Other
# StreamKind/String                : Other
# StreamKindID                     : 2
# StreamKindPos                    : 3
# Type                             : Time code
# Format                           : SMPTE TC
# Format_Commercial                : SMPTE TC
# MuxingMode                       : SDTI
# TimeCode_FirstFrame              : 00:00:00:00


# Transforms MediaInfo output to dict object
# Replacing '/' in key names with '_', removing '(' and ')'
# result:
# { 'General': [{'Format': 'Matroska', 'FrameRate': '23.976', ...}],    == ffprobe's 'format', mandatory
#   'Video': [{...}, ...],                                              == ffprobe's codec_type 'video'
#   'Audio': [{...}, ...],                                              == ffprobe's codec_type 'audio'
#   'Text': [{...}, ...],                                               == ffprobe's codec_type 'subtitle'
#   'Menu': [{...}, ...] }                                              == ffprobe's codec_type 'data'
def mediainfo2dict(mistr):

    header = re.compile(r'^(\w+)\s?#?(\d+)?$')
    record = re.compile(r'^(\w+)\s+:\s+(.*)$')
    current_header = None
    result = {}
    for line in re.split(r'[\r\n]+', mistr):
        hf = header.findall(line)
        if len(hf):
            current_header = hf[0][0]
            if current_header in result:
                if len(hf[0]) != 2 or (int(hf[0][1]) - 1) != len(result[current_header]):
                    # Error!
                    print('Error: failed to parse mediainfo string')
                    print(line)
                    return None
            else:
                result[current_header] = []
            result[current_header].append({})
            continue
        rf = record.findall(line)
        if len(rf) == 1 and len(rf[0]) == 2:
            key = rf[0][0].replace('/', '_').replace('(', '').replace(')', '')
            result[current_header][-1].update({key: guess_type(rf[0][1])})
    return result


# Combine video info dicts captured by FFProbe and MediaInfo using baseclass' definitions
def combine_ffprobe_mediainfo_track(ffv, miv, baseclass):

    inst = baseclass()
    srcdata = {'ff': ffv, 'mi': miv}
    result = {}

    # Enumerate baseclass' members
    for k in inst.__dict__:
        # Get source model for member: the static var named <member>.upper()
        model_name = k.upper()
        if model_name not in baseclass.__dict__:
            continue
        member_model = baseclass.__dict__[model_name]
        for src in member_model['src']:
            # Default value
            # It may be JSONer object, in this case we have to convert it to dict
            val = inst.__dict__[k]
            if isinstance(val, JSONer):
                val = val.__jsoner2dict__()
            if src[1] in srcdata[src[0]]:
                val = srcdata[src[0]][src[1]]
            if val is not None:
                result[k] = val if 'map' not in member_model else member_model['map'][val]
                break
    # Final pass for D10 support
    if 'height_original' in result:
        if result['height_original'] == 0:
            result['height_original'] = result['height']
            result['height_offset'] = 0
        else:
            if result['height'] != result['height_original'] - result['height_offset']:
                print('Warning: height_original == {}, height_offset == {}, height == {} (must be {})'.format(
                    result['height_original'], result['height_offset'], result['height'], result['height_original'] - result['height_offset']
                ))
                result['height'] = result['height_original'] - result['height_offset']
    if 'width' in result and 'height' in result:
        # Sanitize DAR (it may be '0:1')
        if 'dar' in result:
            result['dar'].sanitize(result['width'], result['height'])
        else:
            # TODO: try to use PAR to calculate DAR
            result['dar'] = Rational(result['width'], result['height'])
            result['par'] = Rational(1, 1)
        # Final pass for PAR: calculate PAR from DAR
        if 'par' not in result:
            vdar = result['dar'].val()
            par_str = Rational.search_numerator_denominator(vdar * result['height'] / result['width'], delta=0.001)
            result['par'] = Rational(par_str)
    return result


# Combine info captured by FFProbe and MediaInfo
def combine_ffprobe_mediainfo(ffstr, mistr):
    ffi = json.loads(ffstr, object_hook=object_hook)
    mii = mediainfo2dict(mistr)
    # Workaround absence of 'StreamOrder'
    defaultStreamOrder = None
    if mii['General'][0]['StreamCount'] == 1:
        defaultStreamOrder = 0
    guide = [
        {
            'dst': {'section': 'format', 'list': False, 'class': MediaFile.Format},
            'src': {'mi': 'General', 'ff': 'format'}
        },
        {
            'dst': {'section': 'videoTracks', 'list': True, 'class': MediaFile.VideoTrack},
            'src': {'mi': 'Video', 'index': 'StreamOrder', 'ff':  'streams'}
        },
        {
            'dst': {'section': 'audioTracks', 'list': True, 'class': MediaFile.AudioTrack},
            'src': {'mi': 'Audio', 'index': 'StreamOrder', 'ff':  'streams'}
        },
        {
            'dst': {'section': 'subTracks', 'list': True, 'class': MediaFile.SubTrack},
            'src': {'mi': 'Text', 'index': 'StreamOrder', 'ff':  'streams'}
        },
    ]
    result = {}
    for g in guide:
        if g['src']['mi'] in mii:
            dst = g['dst']
            src_mi = mii[g['src']['mi']]
            src_ff = ffi[g['src']['ff']]
            if dst['list']:
                result[dst['section']] = []
                for track_mi in src_mi:
                    try:
                        index = track_mi[g['src']['index']]
                    except:
                        Logger.debug('Track\'s MediaInfo does not contain StreamOrder, try default: {}\n'.format(defaultStreamOrder), Logger.LogLevel.LOG_WARNING)
                        index = defaultStreamOrder
                    track_ff = src_ff[index]
                    combined_track = combine_ffprobe_mediainfo_track(track_ff, track_mi, dst['class'])
                    result[dst['section']].append(combined_track)
            else:
                result[dst['section']] = combine_ffprobe_mediainfo_track(ffi[g['src']['ff']], mii[g['src']['mi']][0], dst['class'])
    return result


def combined_info(mf: MediaFile, path=None):
    for frame in traceback.extract_tb(sys.exc_info()[2]):
        print(frame)
    if path is None:
        path = mf.source.path
        if path is None:
            return
    ffstr = get_ffprobe_info(path)
    mistr = get_media_info(path)
    combined = combine_ffprobe_mediainfo(ffstr, mistr)
    mf.update_json(combined)
    mf.source.path = path
    if '/' in path:
        mf.name = path.rsplit('/', 1)[1].rsplit('.', 1)[0]
    elif '\\' in path:
        mf.name = path.rsplit('\\', 1)[1].rsplit('.', 1)[0]
    else:
        mf.name = path
    for track in mf.videoTracks + mf.audioTracks + mf.subTracks:
        if track.Duration_ms:
            track.duration = track.Duration_ms / 1000.0


def combined_info_mediafile(url) -> MediaFile:
    mf: MediaFile = MediaFile()
    combined_info(mf, url)
    return mf


# def get_combined_info(filename, probe_gop_size=False, select_standard_fps=True, refine_duration=True):
#     if not os.path.isfile(filename):
#         return None
#     # info_n = get_name_tags(os.path.basename(os.path.splitext(filename)[0]))
#     info_f = get_ffprobe_info(filename, refine_duration)
#     info_m = get_media_info(filename)
#     info = {NAME_TAGS: info_n}
#     info.update(sync_info(info_f, info_m))
#     if select_standard_fps and 'video' in info:
#         for v in info['video']:
#             if 'override' not in v:
#                 v.update({'override': {}})
#             v['override'].update(do_select_standard_fps(v['ffprobe']['r_frame_rate']))
#     if 'video' in info:
#         for v in info['video']:
#             if 'width' in v['ffprobe'] and 'height' in v['ffprobe']:
#                 d = select_definition(v['ffprobe']['width'], v['ffprobe']['height'])
#                 v.update({'resolution': d, 'definition': map_source_resolution(d)})
#     if probe_gop_size and info:
#         do_probe_gop_size(info)
#     # Override cached filename
#     info['format']['ffprobe']['filename'] = filename
#     return info


def test(urls=None):
    if type(urls) is list:
        for url in urls:
            mf = combined_info_mediafile(url)
            Logger.log(mf.dumps(indent=2) + '\n')
    elif type(urls) is str:
        mf = combined_info_mediafile(urls)
        Logger.log(mf.dumps(indent=2) + '\n')
    else:
        mf = MediaFile()
        tr = MediaFile.SubTrack()
        tr.index = 0
        mf.subTracks.append(tr)
        combined_info(mf, '/mnt/server1_id/store/_transit/31070394-2e47-4d3b-b3d7-b38d057bf4f8/31070394-2e47-4d3b-b3d7-b38d057bf4f8.s00.extract.mkv')
        Logger.info(mf.dumps(indent=2) + '\n')
