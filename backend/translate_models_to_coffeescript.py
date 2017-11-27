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
    modules.models.Interaction,
    modules.models.Fileset
]


def translate_models_to_cs(basepath=None, prefix='', suffix='_py'):
    for c in MODELS_TO_TRANSLATE:
        Logger.debug('Translating model {} to coffee\n'.format(c.__name__), Logger.LogLevel.LOG_INFO)
        cs = class_py2coffee(c)
        if basepath:
            script = os.path.join(basepath, '{}{}{}.coffee'.format(prefix, c.__name__, suffix))
            Logger.debug('Writing script file {}\n'.format(script), Logger.LogLevel.LOG_WARNING)
            f = open(script, 'w')
            f.write(cs)
            f.close()
        Logger.debug(cs + '\n', Logger.LogLevel.LOG_NOTICE)


if __name__ == '__main__':
    Logger.set_console_level(Logger.LogLevel.LOG_DEBUG)
    models_dir = os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])), 'interface', 'web', 'js', 'models_py')
    translate_models_to_cs(basepath=models_dir)
