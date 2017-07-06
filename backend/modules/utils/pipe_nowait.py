# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Non-blocking std pipes for Windows
# Thanks to https://stackoverflow.com/questions/34504970/non-blocking-read-on-os-pipe-on-windows

import os
if os.name == 'nt':
    import msvcrt
    from ctypes import windll, byref, wintypes, GetLastError, WinError
    from ctypes.wintypes import HANDLE, DWORD, LPDWORD, BOOL
    PIPE_NOWAIT = wintypes.DWORD(0x00000001)
    ERROR_NO_DATA = 232
else:
    import fcntl


def pipe_nowait(pipe):
    if os.name == 'nt':
        method = windll.kernel32.SetNamedPipeHandleState
        method.argtypes = [HANDLE, LPDWORD, LPDWORD, LPDWORD]
        method.restype = BOOL
        h = msvcrt.get_osfhandle(pipe.fileno())
        res = method(h, byref(PIPE_NOWAIT), None, None)
        if res == 0:
            print(WinError())
            return False
        return True
    flags = fcntl.fcntl(pipe, fcntl.F_GETFL)
    fcntl.fcntl(pipe, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    return True


if __name__ == '__main__':
    # CreatePipe
    r, w = os.pipe()

    pipe_nowait(r)

    print(os.write(w, b'xxx'))
    print(os.read(r, 1024))
    try:
        print(os.write(w, b'yyy'))
        print(os.read(r, 1024))
        print(os.read(r, 1024))
    except OSError as e:
        print('{} {} {}'.format(dir(e), e.errno, GetLastError()))
        print(WinError())
        if GetLastError() != ERROR_NO_DATA:
            raise
