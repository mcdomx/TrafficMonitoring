import queue
from multiprocessing import Queue

from flask_socketio import SocketIO

from modules.threads.logging_thread import LoggingThread
from modules.threads.monitoring_thread import MonitorThread
from modules.threads.video_capture_thread import VideoCaptureThread
from modules.services.parameter_service import ParameterService


class ThreadManager(object):
    """
    Handles starting and stopping all required threads and
    stores the thread references as well as the running status.
    """
    def __init__(self, socketio: SocketIO, buffer_size=256):
        self._threads = {}
        self.all_running = False
        self.socketio = socketio
        self.ps = ParameterService()

        # queues
        self.buffer_size = buffer_size
        self.ref_queue = queue.Queue(buffer_size)  # includes frame num and queue to get frame from
        self.det_queue = queue.Queue(buffer_size)  # includes frames with processed detections
        self.undet_queue = queue.Queue(buffer_size)  # includes frame without detections
        self.detections_queue = queue.Queue(buffer_size)  # includes detections for the logging interval period
        # self.mon_queue = queue.Queue(20)  # used to monitor detections (time, detections:set, image:np.array)
        self.mon_queue = Queue(20)  # used to monitor detections (time, detections:set, image:np.array)

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
        Thread may already been added with add_thread.
        Separating add and start processes allow tighter control of thread starts.
        """
        start_me = self._threads.get(t)

        if not start_me:  # thread was not added, so add it
            self.add_thread(start_me)
            print("'{}' was not an active thread.  Added.".format(t))

        start_me.RUNNING = True
        start_me.start()
        print("THREAD: {} > Started!  {}".format(start_me.getName(), t))

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
        self.clear_all_queues()
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

    def get_qsize(self, queue_name: str) -> int:
        if queue_name == 'ref_queue':
            return self.ref_queue.qsize()
        if queue_name == 'det_queue':
            return self.det_queue.qsize()
        if queue_name == 'undet_queue':
            return self.undet_queue.qsize()
        if queue_name == 'detections_queue':
            return self.detections_queue.qsize()
        if queue_name == 'mon_queue':
            return self.mon_queue.qsize()

    def clear(self, q: str):
        clear_me = None
        if q == 'ref_queue':
            clear_me = self.ref_queue
        if q == 'det_queue':
            clear_me = self.det_queue
        if q == 'undet_queue':
            clear_me = self.undet_queue
        if q == 'detections_queue':
            clear_me = self.detections_queue
        if q == 'mon_queue':
            clear_me = self.mon_queue

        with clear_me.mutex:
            while not clear_me.empty:
                _ = clear_me.get()
                clear_me.task_done()

    def clear_all_queues(self):
        for q in ('ref_queue',
                  'det_queue',
                  'undet_queue',
                  'detections_queue'):  # ,
                  # 'mon_queue'):
            self.clear(q)

        print("Cleared all queues!")

