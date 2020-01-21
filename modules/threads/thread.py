# from abc import ABC
# import threading
#
#
# class Thread(threading.Thread, ABC):
#     """
#     Abstract class for a local thread.
#     required methods:
#     > stop()
#         - sets running to False for each thread causing loops to stop running
#     """
#
#     def __init__(self, name, thread_mgr):
#         threading.Thread.__init__(self)
#         self._name = name
#         self._running = False
#         self.tm = thread_mgr
#
#     def getName(self):
#         return self._name
#
#     def is_running(self):
#         return self._running
#
#     def stop(self):
#         self._running = False
