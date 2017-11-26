# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import os
import re
import sys
from inspect import getsourcefile
from os.path import abspath


def convert(src, dst):
    result = ''
    f1 = re.compile(r'^(\s+[a-zA-Z0-9_\.]+): ([a-zA-Z_\.]+) = ([a-zA-Z_\.]+.*)$')
    f2 = re.compile(r'^(\s+[a-zA-Z0-9_\.]+): ([a-zA-Z_\.]+\[[a-zA-Z_\.]+\]) = (\[.*\].*)$')
    lcount = 0
    rcount = 0
    bcount = 0
    with open(src, 'r') as f:
        text = f.read().replace('\r\n', '\n').split('\n')
        for l in text:
            lcount += 1
            a = f1.findall(l)
            b = f2.findall(l)
            if len(a):
                rcount += 1
                l = '{} = {}'.format(a[0][0], a[0][2])
                # else:
                #     bcount += 1
                #     print('Error in line: {}'.format(l))
            elif len(b):
                rcount += 1
                l = '{} = {}'.format(b[0][0], b[0][2])
            result += l + '\n'
    # print('File: {}, Lines: {}, conforms: {}, bads: {}'.format(os.path.basename(src), lcount, rcount, bcount))
    with open(dst, 'w') as f:
        f.write(result)


def conform():
    dirs = set([])
    srcd = os.path.dirname(abspath(getsourcefile(lambda: 0)))
    dstd_base = sys.argv[1]
    print(srcd)
    if sys.argv[1] == srcd:
        print('Destination dir equals to source dir!')
        exit(1)
    if os.path.sep == '\\':
        rpls = re.compile(r'^' + srcd.replace('.', '\\.').replace('\\', '\\\\'))
    else:
        rpls = re.compile(r'^' + srcd.replace('.', '\\.'))
    for root, dd, files in os.walk(srcd):
        fpy = [_ for _ in files if _.endswith('.py')]
        if len(fpy):
            dstd = rpls.sub(dstd_base, root)
            if dstd == root:
                print('FAIL!')
                exit(1)
            if dstd not in dirs:
                dirs.add(root)
                os.makedirs(dstd, exist_ok=True)
            for f in fpy:
                convert(os.path.join(root, f), os.path.join(dstd, f))


if __name__ == '__main__':
    conform()
