#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import sys
from modules.utils.database import DBInterface


if __name__ == '__main__':
    DBInterface.Asset.records(sys.argv[1:])

