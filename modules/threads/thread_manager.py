from flask_socketio import SocketIO

from modules.threads.logging_thread import LoggingThread
from modules.threads.monitoring_thread import MonitorThread
from modules.threads.video_capture_thread import VideoCaptureThread
from modules.services.queue_service import QueueService
from modules.services.parameter_service import ParameterService


class ThreadManager(object):
    """
    Singleton.
    Handles starting and stopping all required threads and
    stores the thread references as well as the running status.
    """

    # _s = None
    #
    # def __new__(cls, socketio: SocketIO, queue_service, parameter_service):
    #
    #     if cls._s is None:
    #         cls._s = super(ThreadManager, cls).__new__(cls) #.__Singleton(socketio, queue_service, parameter_service)
    #     return cls._s

    # class __Singleton:
    def __init__(self, socketio: SocketIO):
        self._threads = {}
        self.all_running = False
        self.socketio = socketio
        self.qs = QueueService()
        self.ps = ParameterService()

    def status(self):
        for k, v in self._threads.items():
            print("Thread: {}  // {}".format(k, "STARTED" if v.is_running() else "READY TO START"))

    def add_thread(self, t: str):
        """Adding only adds a single thread and does not start it"""
        if t == 'monitor':
            self._threads[t] = MonitorThread("monitoring-thread", self)
        elif t == 'log':
            self._threads[t] = LoggingThread("logging-thread", self)
        elif t == 'video':
            self._threads[t] = VideoCaptureThread("capture-thread", self)
        else:
            print("'{} thread type is not supported!".format(t))

    def add_all_threads(self):
        """
        Add all threads - need to be started after adding
        :return:
        """
        for t in ('monitor', 'log', 'video'):
            self.add_thread(t)

    def start_thread(self, t: str):
        """
        Thread must have already been added with add_thread to be able to start.
        Separating add and start processes allow tighter control of thread starts.
        """
        start_me = self._threads.get(t)

        if start_me:
            start_me.RUNNING = True
            start_me.start()
            print("THREAD: {} > Started!".format(start_me.getName()))
        else:
            print("'{}' is not an active thread.  Nothing started.". format(t))

    def start_all_threads(self):
        """
        Start all threads.  All must be added first.
        :return:
        """
        for t in ('monitor', 'log', 'video'):
            self.start_thread(t)
        self.all_running = True

    def stop_thread(self, t: str):

        stop_me = self._threads.get(t)

        if stop_me:
            # stop_me.RUNNING = False
            print("THREAD: Stopping '{}' ... ".format(stop_me.getName()), end='')
            stop_me.stop()  # signal thread to stop
            self._threads[t] = None
            print("STOPPED!")
        else:
            print("'{}' is not an active thread type. Nothing stopped".format(t))
            return

    def stop_all_threads(self):
        """
        Stop all threads currently active
        :return:
        """
        for t in self._threads:  # capture thread must stop first
            self.stop_thread(t)
        self.all_running = False
        self.qs.clear_all_queues()
        print("All threads stopped!")

    def toggle(self, t: str):

        toggle_me = self._threads.get(t)

        if toggle_me:  # running
            self.stop_thread(t)

        else:  # value is None - means it is not running
            print("calling add thread")
            self.add_thread(t)
            print("calling start thread")
            self.start_thread(t)

    def toggle_all(self):

        if self.all_running:
            # turn all off
            self.stop_all_threads()
        else:
            # turn all on
            self.add_all_threads()
            self.start_all_threads()

    def restart_all(self):
        self.stop_all_threads()
        self.start_all_threads()
