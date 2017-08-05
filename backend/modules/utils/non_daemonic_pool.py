# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


import multiprocessing
# import multiprocessing.Process
import multiprocessing.pool
# import time


class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass

    daemon = property(_get_daemon, _set_daemon)


class NonDaemonicPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess

#
# def sleepawhile(t):
#     print("Sleeping %i seconds..." % t)
#     time.sleep(t)
#     return t


# def work(num_procs):
#     print("Creating %i (daemon) workers and jobs in child." % num_procs)
#     pool = multiprocessing.Pool(num_procs)
#
#     result = pool.map(sleepawhile,
#         [randint(1, 5) for x in range(num_procs)])
#
#     # The following is not really needed, since the (daemon) workers of the
#     # child's pool are killed when the child is terminated, but it's good
#     # practice to cleanup after ourselves anyway.
#     pool.close()
#     pool.join()
#     return result
#
#
# def test():
#     print("Creating 5 (non-daemon) workers and jobs in main process.")
#     pool = MyPool(5)
#
#     result = pool.map(work, [randint(1, 5) for x in range(5)])
#
#     pool.close()
#     pool.join()
#     print(result)
#
#
# if __name__ == '__main__':
#     test()
