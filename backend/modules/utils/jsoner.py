# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import json
import datetime
from .log_console import Logger


# This helper class makes JSON <key:value> be accessible via class members
class JSONer:

    @staticmethod
    def filter(object_dict, expose_unmentioned=False, expose_empty=True, expose_none=False):
        res = {}
        for k in object_dict:
            if k == 'unmentioned' and not expose_unmentioned:
                continue
            v = object_dict[k]
            if not expose_none and v is None:
                continue
            if not expose_empty:
                if (isinstance(v, list) or isinstance(v, dict) or isinstance(v, JSONer)) and len(v) == 0:
                    continue
            if isinstance(v, list):
                vv = []
                for x in v:
                    try:
                        vv.append(x.dump_alt())
                    except:
                        vv.append(x)
                # v = [_.dump_alt() for _ in v]
                v = vv
            else:
                try:
                    v = v.dump_alt()
                except:
                    pass
            res[k] = v
        return res

    @staticmethod
    def subclass_name(member_name, array=False):
        cn = member_name[0].upper() + member_name[1:]
        if array:
            cn = cn[:-1]
        return cn

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

    def __str__(self):
        return self.dumps()

    def __repr__(self):
        return self.dumps()

    def __getitem__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        return self.unmentioned[item]

    def __setitem__(self, item, value):
        self.__dict__[item] = value

    def __iter__(self):
        for k in self.__dict__:
            if k != 'unmentioned':
                yield k
        for k in self.unmentioned:
            yield k

    def dumps(self, ensure_ascii=True, indent=None, separators=None, expose_unmentioned=False, expose_empty=True, expose_none=False):
        # Exclude unmentioned, None and empty lists
        json_string = json.dumps(
            JSONer.filter(self.__dict__, expose_unmentioned=expose_unmentioned, expose_empty=expose_empty, expose_none=expose_none),
            ensure_ascii=ensure_ascii,
            indent=indent,
            separators=separators,
            default=lambda obj: JSONer.filter(obj.__dict__, expose_unmentioned=expose_unmentioned, expose_empty=expose_empty, expose_none=expose_none)
        )
        return json_string

    def _update_member(self, name, val):
        roots = globals()
        # class_name = name[0].upper() + name[1:]
        class_name = JSONer.subclass_name(name)
        # Check if there is a child class with the same name (capitalized)
        #  declared in current class (preferred) or in global space
        subclass = None
        is_root = False
        if class_name in self.__class__.__dict__:
            subclass = self.__class__.__dict__[class_name]
        elif class_name in roots:
            subclass = roots[class_name]
            is_root = True
        if subclass:
            # If so, check default member type:
            # if it has the same type as subclass, update it with val
            if isinstance(self.__dict__[name], subclass):
                self.__dict__[name].update_json(val)
                return
            # if val is a string, lookup subclass member <val> and use it's value for member
            if isinstance(val, str):
                if val in subclass.__dict__:
                    self.__dict__[name] = subclass.__dict__[val]
                    return
                if is_root:
                    Logger.warning(
                        "Class '{pclass}' has member '{mb}', there is '{sclass}' in globals,"
                        " but '{sclass}' has no static member '{val}'\n".format(
                            pclass=self.__class__.__name__,
                            mb=name,
                            sclass=class_name,
                            val=val
                        ))
                else:
                    Logger.warning(
                        "Class '{pclass}' has member '{mb}' and subclass '{sclass}',"
                        " but subclass has no static member '{val}'\n".format(
                            pclass=self.__class__.__name__,
                            mb=name,
                            sclass=class_name,
                            val=val
                        ))
            elif not isinstance(val, int):
                if is_root:
                    Logger.warning(
                        "Class '{pclass}' has member '{mb}', there is '{sclass}' in globals,"
                        " but member is not initialized with '{sclass}'\n".format(
                            pclass=self.__class__.__name__,
                            mb=name,
                            sclass=class_name
                        ))
                else:
                    Logger.warning(
                        "Class '{pclass}' has member {mb} and subclass '{sclass}',"
                        " but member is not initialized with '{sclass}'\n".format(
                            pclass=self.__class__.__name__,
                            mb=name,
                            sclass=class_name
                        ))

        # Check next variants:
        # theClassNames: List[TheClassName] = []
        # theClassNames: List[self.TheClassName] = []
        # Member must be initialized to empty list, and it's name must end with 's' (theClassNames),
        #  and there must be [child] class TheClassName(JSONer)
        if name[-1] == 's':
            # class_name = class_name[:-1]
            class_name = JSONer.subclass_name(name, array=True)
            subclass = None
            is_root = False
            if class_name in self.__class__.__dict__ and isinstance(self.__class__.__dict__[class_name], type(object)):
                subclass = self.__class__.__dict__[class_name]
            elif class_name in roots and isinstance(roots[class_name], type(object)):
                subclass = roots[class_name]
                is_root = True
            if subclass:
                if isinstance(self.__dict__[name], list):
                    if isinstance(val, list):
                        # Create new objects, initialize and store to list
                        for v in val:
                            obj = subclass()
                            obj.update_json(v)
                            self.__dict__[name].append(obj)
                        return
                    if is_root:
                        Logger.warning(
                            "Class '{pclass}' has member '{mb}' initialized as list,"
                            " and there is '{sclass}' in globals, but supplied JSON object is {jtype}\n".format(
                                pclass=self.__class__.__name__,
                                mb=name,
                                sclass=class_name,
                                jtype=type(val)
                            ))
                    else:
                        Logger.warning(
                            "Class '{pclass}' has member '{mb}' initialized as list,"
                            " and subclass '{sclass}', but supplied JSON object is {jtype}\n".format(
                                pclass=self.__class__.__name__,
                                mb=name,
                                sclass=class_name,
                                jtype=type(val)
                            ))
                else:
                    if is_root:
                        Logger.warning(
                            "Class '{pclass}' has member '{mb}' and there is '{sclass}' in globals,"
                            " but member is not initialized as list\n".format(
                                pclass=self.__class__.__name__,
                                mb=name,
                                sclass=class_name
                            ))
                    else:
                        Logger.warning(
                            "Class '{pclass}' has member '{mb}' and subclass '{sclass}',"
                            " but member is not initialized as list\n".format(
                                pclass=self.__class__.__name__,
                                mb=name,
                                sclass=class_name
                            ))
        # Simply set member value
        if isinstance(val, datetime.datetime):
            self.__dict__[name] = str(val)
        else:
            self.__dict__[name] = val

    # Update object by JSON
    def update_json(self, json_obj):
        # Enumerate child class' members
        for k in self.__dict__:
            if json_obj.__contains__(k):
                val = json_obj.pop(k)
                try:
                    self._update_member(k, val)
                except Exception as e:
                    Logger.error('Failed to update member {} with {}\n'.format(k, val))
                    exit(1)
        self.unmentioned.clear()
        for k in json_obj:
            self.unmentioned[k] = json_obj[k]

    def update_str(self, json_str):
        a = json.loads(json_str)
        self.update_json(a)

    def get_members_set(self):
        result = set(self.__dict__.keys())
        result.remove('unmentioned')
        return result

    def get_members_list(self):
        result = [m for m in self.__dict__ if m != 'unmentioned']
        return result

    def full_instance(self):
        roots = globals()
        for name in self.__dict__:
            # Subclass members should be already initialized

            # Check next variants:
            # theClassNames: List[TheClassName] = []
            # theClassNames: List[self.TheClassName] = []
            # Member must be initialized to empty list, and it's name must end with 's' (theClassNames),
            #  and there must be [child] class TheClassName(JSONer)
            if name[-1] == 's':
                class_name = JSONer.subclass_name(name, array=True)
                subclass = None
                if class_name in self.__class__.__dict__ and isinstance(self.__class__.__dict__[class_name], type(object)):
                    subclass = self.__class__.__dict__[class_name]
                elif class_name in roots and isinstance(roots[class_name], type(object)):
                    subclass = roots[class_name]
                if subclass:
                    if isinstance(self.__dict__[name], list):
                        obj = subclass()
                        obj.full_instance()
                        self.__dict__[name].append(obj)

    def reset_lists(self):
        for k in self.__dict__:
            if type(self.__dict__[k]) is list:
                self.__dict__[k].clear()
