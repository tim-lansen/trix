# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import re
import os
import sys
import copy
import time
from typing import List
from modules.models.mediafile import MediaFile
try:
    import fcntl
    DEVNULL = '/dev/null'
except:
    DEVNULL = 'nul'
    pass


def ffmpeg_create_reference_extract_audio_subtitles(info: MediaFile):
    """
    ffmpeg -i <src> -map v:0 -vsync 1 -vf fps=<closest standard fps>,<analyzing filters> -c:v rawvideo -f rawvideo - ^
    |ffmpeg <setup> -loglevel error -i - -pix_fmt yuv420p -vf scale=<ref size>
    :param info:
    :return:
    """
    src = info.source.url
    vout_arch: List[MediaFile] = []
    vout_refs: List[MediaFile] = []
    # Enumerate video tracks, collect transformation filters
    for i, v in enumerate(info.videoTracks):
        arch = MediaFile()
        va = copy.deepcopy(v)
        arch.videoTracks.append(va)
        vout_arch.append(arch)
        vout_refs.append(va.ref_add())
        filters_ref = '[v]sca'
    # Calculate preview video dimensions
    # pvdata = utils.fit_video_with_aspect(info['video'][type_index]['ffprobe'], display_w, display_h, preview_scale)
    # filters = ['cropdetect=20:2:40']
    # if pvdata['preview_width'] != info['video'][type_index]['ffprobe']['width'] or pvdata['preview_height'] != info['video'][type_index]['ffprobe']['height']:
    #     filters += ['scale={0}:{1}'.format(pvdata['preview_width'], pvdata['preview_height'])]
    # info['video'][type_index]['preview_size'] = pvdata
    # ref_video = output
    # os.path.join(output_dir, '{0}.{1}.{2}.mp4'.format(output_name, xii, xtype_index))
    command = 'ffmpeg -y -i {src}, '-i', utils.BRICK_PNG,
        '-filter_complex',
        '[0:v:{}]{1}[s],[s][1:v]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2:enable=\'gt(t,{2})\''
        ',blackdetect=d=0.5:pic_th=0.99:pix_th=0.005'
        ',showinfo[v]'
        ''.format(type_index, ','.join(filters), dur - 3.0),
        '-map', '[v]',
        '-vcodec', 'libx264', '-preset', 'fast', '-g', '20', '-b:v', '320k',
        output]
    if extract_audio:
        command += extract_audio
    print ' '.join(command)
    proc = Popen(command, stdin=sys.stdin, stderr=PIPE)
    # 'blacks' will contain pairs [in, dur] of black
    blacks = []
    # 'frames' will contain filtered showinfo
    frames = {'iframes': [], 'frames': []}
    # 'crop' contains current crop
    # 'crops' will contain crop changes and PTS
    pts_time = 0.0
    crop_w = {'w': -1, 'x': 0}
    crop_h = {'h': -1, 'y': 0}
    crops = []
    while proc.poll() is None:
        cap = proc.stderr.readline()
        for line in cap.strip().split('\r'):
            if line.startswith('[blackdetect'):
                parse = parse_ffmpeg_vf_blackdetect(line)
                if parse:
                    blacks.append([parse['black_start'], parse['black_end']])
            elif line.startswith('[Parsed_showinfo'):
                parse = parse_ffmpeg_vf_showinfo(line)
                if parse:
                    pts_time = parse['pts_time']
                    if parse['iskey'] == 1:
                        # sys.stderr.write('\x1b[0;1;31m' + line + '\x1b[0m\n')
                        frames['iframes'].append(parse)
                    # frames['frames'].append(parse)
            elif line.startswith('[Parsed_cropdetect'):
                parse = parse_ffmpeg_vf_cropdetect(line)
                if parse:
                    update = False
                    if 'w' in parse:
                        if crop_w['w'] != parse['w'] or crop_w['x'] != parse['x']:
                            crop_w = {'w': parse['w'], 'x': parse['x']}
                            update = True
                    if 'h' in parse:
                        if crop_h['h'] != parse['h'] or crop_h['y'] != parse['y']:
                            crop_h = {'h': parse['h'], 'y': parse['y']}
                            update = True
                    if update:
                        crop_w.update(crop_h)
                        crops.append({'pts_time': pts_time, 'crop': crop_w})
            elif line.startswith('frame='):
                sys.stderr.write(line + '\r')
    return {'blacks': blacks, 'crops': crops, 'frames': frames}
