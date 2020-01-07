from flask_socketio import SocketIO

from modules.threads.logging_thread import LoggingThread
from modules.threads.monitoring_thread import MonitorThread
from modules.threads.video_capture_thread import VideoCaptureThread


class ThreadManager:
    """
    Singleton.
    Handles starting and stopping all required threads and
    stores the thread references as well as the running status.
    """

    singleton = None

    def __new__(cls, socketio: SocketIO):
        if cls.singleton is None:
            cls.singleton = cls.__Singleton(socketio)
        return cls.singleton

    class __Singleton:
        def __init__(self, socketio: SocketIO):
            self._threads = None
            self.all_running = False
            self._socketio = socketio

        def start_threads(self):
            self._threads = [VideoCaptureThread("capture-thread"),
                             LoggingThread("logging-thread", self._socketio),
                             MonitorThread("monitoring-thread")]
            for t in self._threads:
                t.start()
                print("THREAD: {} > Started!".format(t.getName()))
            self.all_running = True

        def terminate_threads(self):
            for t in self._threads:  # capture thread must stop first
                print("THREAD: Stopping '{}' ... ".format(t.getName()), end='')
                t.stop()  # signal thread to stop
                t.join()  # wait until it is stopped
                print("stopped!")

            self._threads = None
            self.all_running = False
            print("All threads stopped!")

