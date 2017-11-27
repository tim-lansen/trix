# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import os
import platform
from subprocess import Popen
from .record import *


class Node(Record):
    class Status:
        IDLE = 1
        BUSY = 2
        OFFER = 3
        EXITING = 4
        FINISHING = 5
        INVALID = 6

    class Abilities:
        COMBINED_INFO = 0x0001
        FFMPEG = 0x0002
        FFMPEG_NVENC_H264 = 0x0004
        FFMPEG_NVENC_HEVC = 0x0008
        X264_08 = 0x0010
        X264_10 = 0x0020
        X265_08 = 0x0040
        X265_10 = 0x0080
        X265_12 = 0x0100
        X26X = X264_08 | X264_10 | X265_08 | X265_10 | X265_12
        SOX = 0x0200
        MP4BOX = 0x0400
        TRIM = 0x0800

        CACHE = 0x8000

        checklist = {
            COMBINED_INFO:     [['ffprobe', 1], ['mediainfo', 255]],
            FFMPEG:            [['ffmpeg', 1]],
            FFMPEG_NVENC_H264: [['ffmpeg -y -loglevel error -filter_complex smptehdbars=size=hd1080 -t 1 -c:v nvenc_h264 -f null {}'.format(os.devnull), 0]],
            FFMPEG_NVENC_HEVC: [['ffmpeg -y -loglevel error -filter_complex smptehdbars=size=4k -t 1 -c:v nvenc_hevc -f null {}'.format(os.devnull), 0]],       # 4k == 4096x2160
            X264_08:           [['x264.08', 255]],
            X264_10:           [['x264.10', 255]],
            X265_08:           [['x265.08', 1]],
            X265_10:           [['x265.10', 1]],
            X265_12:           [['x265.12', 1]],
            SOX:               [['sox', 1]],
            MP4BOX:            [['MP4Box', 1]],
            TRIM:              [['trim.out', 255]]
        }

    def __init__(self):
        super().__init__()
        self.job = None
        self.job_types = None
        self.status = Node.Status.IDLE
        self.channel = None
        self.progress = None

        self.abilities = 0

    TABLE_SETUP = {
        "relname": "trix_nodes",
        "fields": [
            ["status", "integer NOT NULL"],
            ["channel", "name NOT NULL"],
            ["job_types", "integer[]"],
            ["job", "uuid"],
            ["progress", "double precision"],
            ["abilities", "integer NOT NULL"]
        ],
        "fields_extra": [
            ["CONSTRAINT node_name_is_unique UNIQUE", "name"]
        ],
        "creation": [
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }


