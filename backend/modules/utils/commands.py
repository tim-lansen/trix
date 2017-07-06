# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Various command utils


def format_command(params: list) -> str:
    string = ''
    for t in params:
        if len(t):
            if ' ' in t:
                string += '"{0}" '.format(t.replace('"', '\\"'))
            else:
                string += '{0} '.format(t)
    return string
