import os
import re
import sys
import xml.etree.ElementTree as ET


def main():
    if not os.path.isdir(sys.argv[1]):
        print('Give me a DIRECTORY')
        exit(1)
    tdir = sys.argv[1]
    with open(os.path.join(tdir, 'manifest'), 'r') as f:
        manifest = f.read()
    mx = ET.fromstring(manifest)

    pt = re.compile(r' d\=\"(\d+)\"')
    new_man =

    # timescales = []
    #
    # def _scan_ismc(e, d):
    #     name = e.tag.rsplit('}', 1)[-1].strip()
    #     # print '..'*d + name, e.attrib, e.text
    #     if name == 'SmoothStreamingMedia':
    #         dick['streams'] = []
    #         # dick['timescale'] = int(e.attrib['Timescale'])
    #         dick['duration'] = int(e.attrib['Duration'])
    #     elif name == 'StreamIndex':
    #         # new stream
    #         dick['streams'].append({'type': e.attrib['Type'],
    #                                 'lang': get_val(e.attrib, 'Language'),
    #                                 'name': get_val(e.attrib, 'Name'),
    #                                 'url': e.attrib['Url'].replace('{bitrate}', '{0}').replace('{start time}', '{1}'),
    #                                 'bitrates': [],
    #                                 'timeline': []})
    #         for x in e:
    #             name = x.tag.rsplit('}', 1)[-1].strip()
    #             if name == 'QualityLevel':
    #                 dick['streams'][-1]['bitrates'].append(x.attrib['Bitrate'])
    #             elif name == 'c':
    #                 dick['streams'][-1]['timeline'].append(int(x.attrib['d']))
    #         return
    #     d += 1
    #     for c in e:
    #         _scan_ismc(c, d)

    ptrn = re.compile(r'^(Fragments\(.+)\=(\d+)\)$')

    for qdir in os.listdir(tdir):
        if qdir.startswith('QualityLevels'):
            pqdir = os.path.join(tdir, qdir)
            for fn in os.listdir(pqdir):
                old_path = os.path.join(pqdir, fn)

                if os.path.isfile(old_path):
                    q = ptrn.findall(fn)
                    if len(q) == 1 and len(q[0]) == 2 and len(q[0][1]) > 4:
                        new_fn = '{}={})'.format(q[0][0], q[0][1][:-4])
                        new_path = os.path.join(pqdir, new_fn)
                        print('{} -> {}'.format(fn, new_fn))
                        os.rename(old_path, new_path)

if __name__ == '__main__':
    main()
