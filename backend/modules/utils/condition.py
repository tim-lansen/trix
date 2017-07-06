# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Test condition
# Condition is a string of real code condition
# "job."
# ["info.video.0.ffprobe.width", 1280, ">=", "info.video.0.ffprobe.height", 720, ">=", "||"]
# object is an object that contains all necessary data


def condition_is_true(condition: str, **objects):
    cond = condition.replace('__', '')
    result = False
    try:
        result = eval(cond, objects)
    except Exception as e:
        print(e)
    return result


def test():
    class RootClass:
        def __init__(self):
            self.abc = 0
            self.cc = self.ChildClass1()

        class ChildClass1:
            def __init__(self):
                self.abc = 1
                self.cc = self.ChildClass2()

            class ChildClass2:
                def __init__(self):
                    self.abc = 2

    root = RootClass()
    print(condition_is_true('obj1.abc < obj2.abc or obj2.cc.abc < obj1.cc.abc', **{'obj1': root, 'obj2': root.cc}))


if __name__ == '__main__':
    test()
