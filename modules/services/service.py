from abc import ABC


class Service(ABC):
    """
    Abstract class for a local thread.
    required methods:
    > stop()
        - sets running to False for each thread causing loops to stop running
    """

    def __init__(self, name):
        self._name = name
        self._running = False

    def getName(self):
        return self._name

    def is_running(self):
        return self._running

    def stop(self):
        self._running = False

    def start(self):
        raise Exception("start() must be implemented for each service")
