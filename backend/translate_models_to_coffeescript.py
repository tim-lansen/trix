# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import os
import sys
import modules.models
from modules.utils.class_py2coffee import class_py2coffee
from modules.utils.log_console import Logger


MODELS_TO_TRANSLATE = [
    modules.models.Asset,
    modules.models.MediaFile,
]


def translate_models_to_cs(basepath=None, prefix='py_', suffix='_class'):
    for c in MODELS_TO_TRANSLATE:
        Logger.log('Translating model {} to coffee\n'.format(c.__name__))
        cs = class_py2coffee(c)
        if basepath:
            script = os.path.join(basepath, '{}{}{}.coffee'.format(prefix, c.__name__, suffix))
            Logger.log('Writing script file {}\n'.format(script))
            f = open(script, 'w')
            f.write(cs)
            f.close()
        Logger.info(cs + '\n')


if __name__ == '__main__':
    Logger.set_level(Logger.LogLevel.INFO)
    models_dir = os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])), 'interface', 'web', 'js', 'models')
    translate_models_to_cs(basepath=models_dir)