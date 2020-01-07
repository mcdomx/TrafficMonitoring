from abc import ABC
import threading

from modules.services.queue_service import QueueService
from modules.services.parameters import Params


class Thread(threading.Thread, ABC):
    """
    Abstract class for a local thread.
    required methods:
    > stop()
        - sets running to False for each thread causing loops to stop running
    """

    # threads = []
    # all_running = False
    #
    # @classmethod
    # def terminate_threads(cls):
    #     for t in cls.threads:  # capture thread must stop first
    #         print("THREAD: Stopping '{}' ... ".format(t.getName()), end='')
    #         t.stop()  # signal thread to stop
    #         t.join()  # wait until it is stopped
    #         print("stopped!")
    #
    #     Thread.all_running = False
    #     print("All threads stopped!")

    def __init__(self, name):
        threading.Thread.__init__(self)
        self._name = name
        self._running = False
        self._qs = QueueService()
        self._p = Params()
        # Thread.threads.append(self)
        # self.start()
        # print("THREAD: {} > Started!".format(self._name))

        # if len(Thread.threads) >= 3:
        #     Thread.all_running = True
        #     print("All threads running!")

    def getName(self):
        return self._name

    def stop(self):
        self._running = False




