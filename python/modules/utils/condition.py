# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Test condition
# Condition is a string of real code condition
# "job."
# ["info.video.0.ffprobe.width", 1280, ">=", "info.video.0.ffprobe.height", 720, ">=", "||"]
# object is an object that contains all necessary data


def condition_is_true(condition, **objects):
    return eval(condition, objects)
