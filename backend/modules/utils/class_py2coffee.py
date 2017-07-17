# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import json
from .jsoner import JSONer


def class_py2coffee(Class):
    inst = Class()
    inst.full_instance()
    result = ''
    obj_json = json.loads(inst.dumps(expose_none=True))
    # print(json.dumps(obj_json, indent=2))

    # classes = {}
    classes_list = [{
        'name': Class.__name__,
        'class': obj_json
    }]

    # def _dig_(_cl_, _store_, _base_):
    def _dig_(_cl_, _base_):
        for _m_ in _cl_:
            _v_ = _cl_[_m_]
            if type(_v_) is list:
                if len(_v_) and type(_v_[0]) is dict:
                    # List of subclass instances
                    _new_base_ = _base_ + [JSONer.subclass_name(_m_, array=True)]
                    subclass_name = '_'.join(_new_base_)
                    classes_list.append({
                        'name': subclass_name,
                        'class': _v_[0]
                    })
                    # _store_[_m_] = [{subclass_name: {}}]
                    # _dig_(_v_[0], _store_[_m_][0][subclass_name], _new_base_)
                    _dig_(_v_[0], _new_base_)
                    continue
                # _store_[_m_] = []
            elif type(_v_) is dict:
                if len(_v_):
                    _new_base_ = _base_ + [JSONer.subclass_name(_m_, array=False)]
                    subclass_name = '_'.join(_new_base_)
                    classes_list.append({
                        'name': subclass_name,
                        'class': _v_
                    })
                    # _store_[_m_] = {subclass_name: {}}
                    # _dig_(_v_, _store_[_m_][subclass_name], _new_base_)
                    _dig_(_v_, _new_base_)
                    continue
            #     _store_[_m_] = {}
            # else:
            #     _store_[_m_] = None

    # _dig_(obj_json, classes, [Class.__name__])
    _dig_(obj_json, [Class.__name__])

    for i in range(len(classes_list)):
        desc = classes_list[-1-i]
        result += '\n\nclass {}\n    constructor: () ->\n'.format(desc['name'])
        for m in desc['class']:
            v = desc['class'][m]
            if type(v) is dict:
                result += '        @{} = {{}}\n'.format(m)
            elif type(v) is list:
                result += '        @{} = []\n'.format(m)
            elif type(v) is int:
                result += '        @{} = {}\n'.format(m, v)
            elif type(v) is str:
                result += '        @{} = "{}"\n'.format(m, v)
            else:
                result += '        @{} = null  # {}\n'.format(m, v)

    print(result)

    # print(json.dumps(classes, indent=2))
    # print(json.dumps(classes_list, indent=2))
