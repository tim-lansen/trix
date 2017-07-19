# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import re
import uuid
from .log_console import Logger


class Guid:
    Zero = uuid.UUID(int=0)

    @staticmethod
    def probe(s: str):
        try:
            uuid.UUID(s)
        except:
            return False
        return True

    # Guid may be initialized with string
    # To get new unique GUID pass 0 to value
    def __init__(self, value=None):
        if value is None:
            self.guid = uuid.UUID(int=0)
        elif value == 0:
            self.guid = uuid.uuid4()
        else:
            self.guid = uuid.UUID(value)

    def new(self):
        self.guid = uuid.uuid4()

    def set(self, value):
        self.guid = uuid.UUID(value)

    def dump_alt(self):
        # return None if self.is_null() else str(self.guidx)
        return str(self.guid)

    def update_json(self, v):
        self.guid = uuid.UUID(v)

    def is_null(self):
        return self.guid == self.Zero

    def full_instance(self):
        pass


class Rational:
    RECAP = re.compile(r'^(\d+)([/:])(\d+)$')

    @staticmethod
    def probe(s: str):
        if type(s) is str and Rational.RECAP.match(s):
            return True
        return False

    @staticmethod
    def search_numerator_denominator(v, delta=None, delim=':'):
        if isinstance(v, str) and re.match('^(\d)+:(\d)+$', v):
            n, d = v.split(':')
            v = float(n) / float(d)
            # return v
        else:
            v = float(v)
        if not delta:
            delta = pow(10.0, -min(6, len(str(v).split('.')[1])))
        # print(v, delta)
        sn = int(max(v, 1.0))
        sd = int(max(1.0/v, 1.0))
        n = 1.0
        d = 1.0
        # imd = delta + 1.0
        while True:
            s = sn
            while True:
                imv = n / d
                if v <= imv:
                    break
                imd = v - imv
                if imd <= delta:
                    break
                n += s
                s = 1.0
            s = sd
            while True:
                imv = n / d
                if v >= imv:
                    break
                imd = imv - v
                if imd <= delta:
                    break
                d += s
                s = 1.0
            imd = abs(v - imv)
            if imd <= delta:
                break
            # print(n, d, imv)
        v = '{0}{1}{2}'.format(int(n), delim, int(d))
        # print(v)
        return v

    ## args may be:
    #    a string, example: '24000/1001'
    #    numerator, denominator
    #    numerator, denominator, separator
    def __init__(self, *args):
        self._n = 1
        self._d = 1
        self._s = ':'
        if len(args) == 1:
            if type(args[0]) is str:
                m = Rational.RECAP.findall(args[0])
                if len(m) == 1 and len(m[0]) == 3:
                    self._n = int(m[0][0])
                    self._d = int(m[0][2])
                    self._s = m[0][1]
                else:
                    Logger.error('Rational: bad rational\n', *args)
            else:
                Logger.error('Rational: bad arg\n', *args)
        elif len(args) in {2, 3}:
            if type(args[0]) is int and type(args[1]) is int:
                self._n = args[0]
                self._d = args[1]
                if len(args) == 3:
                    if type(args[2]) is str and len(args[2]) == 1:
                        self._s = args[2]
                    else:
                        Logger.warning('Rational: bad separator\n', *args)
            else:
                Logger.error('Rational: bad args\n', *args)
        else:
            Logger.info('Rational: default\n')
        self._v = 1.0 * self._n
        self._calc()

    def _calc(self):
        try:
            self._v = self._n / self._d
        except:
            Logger.error('Rational: bad denominator ({})\n'.format(self._d))
            self._d = 1

    def val(self):
        return self._v

    def get(self):
        return [self._n, self._d]

    def dump_alt(self):
        return self.__str__()

    def __str__(self):
        return '{n}{s}{d}'.format(n=self._n, s=self._s, d=self._d)


def guess_type(v):
    try:
        x = int(v)
        return x
    except:
        pass
    try:
        x = float(v)
        return x
    except:
        pass
    if Rational.probe(v):
        return Rational(v)
    if Guid.probe(v):
        return Guid(v)
    return v


def test():
    Logger.LOG_CONSOLE_LIKE_FILE = True
    r = Rational('24000/1001')
    print(r.dump_alt())
    r = Rational(24000, 1001)
    print(r.dump_alt())
    r = Rational(24000, 1001, '/')
    print(r.dump_alt())

    r = Rational(24000, '/q')
    print(r.dump_alt())
    r = Rational(24, 0)
    print(r.dump_alt())
    r = Rational()
    print(r.dump_alt())

    Rational.search_numerator_denominator(30000/1001)#, 0.000001)


if __name__ == '__main__':
    test()
