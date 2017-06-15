# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import json
from .log_console import Logger


# This helper class makes JSON <key:value> be accessible via class members
class JSONer(object):

    @staticmethod
    def filter(sd, expose=False):
        res = {}
        for k in sd:
            if not expose and k == 'unmentioned':
                continue
            v = sd[k]
            if v is None:
                continue
            if (isinstance(v, list) or isinstance(v, dict) or isinstance(v, JSONer)) and len(v) == 0:
                continue
            res[k] = v
        return res

    def __init__(self):
        self.unmentioned = {}

    def __len__(self):
        # Return 1 if any data present
        sd = self.__dict__
        for k in sd:
            if k == 'unmentioned':
                continue
            v = sd[k]
            if v is None:
                continue
            if (isinstance(v, list) or isinstance(v, dict) or isinstance(v, JSONer)) and len(v) == 0:
                continue
            return 1
        return 0

    def dumps(self, ensure_ascii=True, indent=None, separators=None, expose_unmentioned=False):
        # Exclude unmentioned, None and empty lists
        json_string = json.dumps(
            JSONer.filter(self.__dict__),
            ensure_ascii=ensure_ascii,
            indent=indent,
            separators=separators,
            default=lambda obj: JSONer.filter(obj.__dict__, expose=expose_unmentioned)
        )
        return json_string

    # Update object by JSON
    def update_json(self, json_obj):
        # Enumerate child class' members
        for k in self.__dict__:
            if json_obj.__contains__(k):
                val = json_obj.pop(k)
                class_name = k[0].upper() + k[1:]
                # Check if there is a child class with the same name (capitalized) declared in current class
                if class_name in self.__class__.__dict__:
                    # If so, check default member type:
                    # if it's type is the class declared, update it with val
                    if isinstance(self.__dict__[k], self.__class__.__dict__[class_name]):
                        self.__dict__[k].update_json(val)
                        continue
                    Logger.warning(
                        "Class {pclass} has member {mb} and subclass {sclass}, but member is not initialized with {sclass}\n".format(
                            pclass=self.__class__.__name__,
                            mb=k,
                            sclass=class_name
                        ))
                # Check list variant: member should be ended with 's' and initialized to empty list (members = []), and there should be declared a child class Member(JSONer)
                if class_name[-1] == 's':
                    class_name = class_name[:-1]
                    if class_name in self.__class__.__dict__ and isinstance(self.__class__.__dict__[class_name], type(object)):
                        if isinstance(self.__dict__[k], list):
                            if isinstance(val, list):
                                for v in val:
                                    obj = self.__class__.__dict__[class_name]()
                                    obj.update_json(v)
                                    self.__dict__[k].append(obj)
                                continue
                            Logger.warning(
                                "Class {pclass} has member {mb} initialized with 'list', and subclass {sclass}, but supplied JSON object is {jtype}\n".format(
                                    pclass=self.__class__.__name__,
                                    mb=k,
                                    sclass=class_name,
                                    jtype=type(val)
                                ))
                        else:
                            Logger.warning(
                                "Class {pclass} has member {mb} and subclass {sclass}, but member is not initialized with 'list'\n".format(
                                    pclass=self.__class__.__name__,
                                    mb=k,
                                    sclass=class_name
                                ))
                # Simply set member value
                self.__dict__[k] = val
        self.unmentioned.clear()
        for k in json_obj:
            self.unmentioned[k] = json_obj[k]

    def update_str(self, json_str):
        a = json.loads(json_str)
        self.update_json(a)

    def get_members(self):
        result = set(self.__dict__.keys())
        result.remove('unmentioned')
        return result

    def get_members_list(self):
        result = [m for m in self.__dict__.keys() if m != 'unmentioned']
        return result


