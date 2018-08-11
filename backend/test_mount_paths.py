#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


from modules.utils.mount_paths import test_mount_paths
from modules.utils.storage import test_storage


if __name__ == '__main__':
    test_mount_paths({'cache'})
    # test_storage()
