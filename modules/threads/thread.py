from abc import ABC
import threading

from modules.services.queue_service import QueueService


class Thread(threading.Thread, ABC):
    """
    Abstract class for a local thread.
    required methods:
    > stop()
        - sets running to False causing loops to stop running
    """

    threads = []

    @classmethod
    def terminate_threads(cls):
        for t in cls.threads[::-1]:
            print("Closing '{}' ... ".format(t.getName()), end='\r')
            t.stop()  # signal thread to stop
            t.join()  # wait until it is stopped
            print("'{}' closed!     ".format(t.getName()))

    def __init__(self, name):
        threading.Thread.__init__(self)
        self._name = name
        self._running = False
        self._qs = QueueService()
        Thread.threads.append(self)
        self.start()

    def getName(self):
        return self._name

    def stop(self):
        print("Stopping thread: ", self.getName())
        self._running = False

