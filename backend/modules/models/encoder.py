# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import uuid
from typing import List
from .record import *


class Parameter(JSONer):

    class Type:
        NAME_ONLY = 1
        VALUE_ONLY = 2
        NAME_AND_VALUE = 3

    def __init__(self):
        super().__init__()
        self.type = self.Type.NAME_AND_VALUE
        self.name: str = None
        # self.no_value = False
        self.value: str = None
        # self.value_default = None

    def command(self):
        if self.type == self.Type.NAME_ONLY:
            assert(isinstance(self.name, str))
            return self.name
        if self.type == self.Type.VALUE_ONLY:
            assert(isinstance(self.value, str))
            return self.value
        if self.type == self.Type.NAME_AND_VALUE:
            assert (isinstance(self.name, str))
            assert (isinstance(self.value, str))
            return '{} {}'.format(self.name, self.value)
        assert()


class Encoder(Record):

    class Input(Parameter):
        def __init__(self):
            super().__init__()

    class Output(Parameter):
        def __init__(self):
            super().__init__()

    class Param(Parameter):
        def __init__(self):
            super().__init__()

    def __init__(self, name):
        super().__init__(name)
        self.alias = None
        self.inputs: List[self.Input] = []
        self.params: List[self.Param] = []
        # in case of multi-output ffmpeg all params is stored in output
        self.outputs: List[self.Output] = []
        self.pattern = '{alias} {inputs} {outputs}'

    def command(self):
        p = {
            'alias': self.name if self.alias is None else self.alias,
            'inputs': ' '.join([_.command() for _ in self.inputs]),
            'params': ' '.join([_.command() for _ in self.params]),
            'outputs': ' '.join([_.command() for _ in self.outputs])
        }
        c = self.pattern.format(**p)
        return c

    # Table description
    TABLE_SETUP = {
        "relname": "trix_encoders",
        "fields": [
            ["alias", "name"],
            ["inputs", "json[]"],
            ["params", "json[]"],
            ["outputs", "json[]"]
        ],
        "fields_extra": [],
        "creation": [
            "GRANT INSERT, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {node};",
            "GRANT INSERT, DELETE, SELECT, UPDATE, TRIGGER ON TABLE public.{relname} TO {backend};"
        ]
    }


if __name__ == '__main__':
    encoder = Encoder('X264')
    encoder.pattern = '{alias} {outputs} {params} {inputs}'
    encoder.inputs = '{}'