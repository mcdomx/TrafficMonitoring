import numpy as np
from multiprocessing import Process

from flask_socketio import SocketIO

from modules.services.monitoring_service import MonitorService
from modules.services.logging_service import LoggingService
from modules.services.video_service import VideoService
from modules.services.service import Service
from modules.services.parameter_service import ParameterService


class ServiceManager(object):
    """
    Handles starting and stopping all required services.
    Acts as interface to underlying services.
    """
    def __init__(self, socketio: SocketIO):
        self.all_running = False
        self.socketio = socketio
        self.ps = ParameterService()
        self._monitor_service: MonitorService = self.get_monitor_service()
        self._logging_service: LoggingService = self.get_logging_service()
        self._video_service: VideoService = self.get_video_service()

    def get_frame(self) -> (bool, np.array):
        success, image, detections, time_stamp = self._video_service.get_next_frame()

        if not success:
            return False, None

        if detections:
            p_mon = Process(target=self._monitor_service.evaluate,
                            args=(image, detections, time_stamp))
            p_log = Process(target=self._logging_service.log_detections,
                            kwargs={'detections': detections})
            p_mon.start()
            p_log.start()
            p_mon.join()
            p_log.join()

        return True, image

    def get_monitor_service(self, name=None, dpm=None, mon_objs=None, mon_dir=None):
        if not name:
            name = "monitor-service"
        if not dpm:
            dpm = self.ps.DPM
        if not mon_objs:
            mon_objs = self.ps.MON_OBJS
        if not mon_dir:
            mon_dir = self.ps.MON_DIR
        print("SERVICE: Adding '{}'".format(name))
        return MonitorService(name, dpm, mon_objs, mon_dir)

    def get_logging_service(self, name=None, dpm=None, log_filepath=None, socketio=None):
        if not name:
            name = "logging-service"
        if not dpm:
            dpm = self.ps.DPM
        if not log_filepath:
            log_filepath = self.ps.LOG_FILEPATH
        if not socketio:
            socketio = self.socketio
        print("SERVICE: Adding '{}'".format(name))
        return LoggingService(name, dpm, log_filepath, socketio)

    def get_video_service(self, name=None,
                          detector_name=None,
                          detector_model=None,
                          base_delay=None,
                          cam_fps=None,
                          cam_stream=None,
                          display_fps=None,
                          dpm=None):
        if not name:
            name = "video-service"
        if not detector_name:
            detector_name = self.ps.DETECTOR_NAME,
        if not detector_model:
            detector_model = self.ps.DETECTOR_MODEL,
        if not base_delay:
            base_delay = self.ps.BASE_DELAY,
        if not cam_fps:
            cam_fps = self.ps.CAM_FPS,
        if not cam_stream:
            cam_stream = self.ps.CAM_STREAM,
        if not display_fps:
            display_fps = self.ps.DISPLAY_FPS,
        if not dpm:
            dpm = self.ps.DPM
        print("SERVICE: Adding '{}'".format(name))
        return VideoService(name=name,
                            detector_name=detector_name,
                            detector_model=detector_model,
                            base_delay=base_delay,
                            cam_fps=cam_fps,
                            cam_stream=cam_stream,
                            display_fps=display_fps, dpm=dpm)

    def add_service(self, s: str) -> Service:
        if s == "monitoring":
            self._monitor_service = self.get_monitor_service()
            return self._monitor_service
        elif s == "logging":
            self._logging_service = self.get_logging_service()
            return self._logging_service
        elif s == "video":
            self._video_service = self.get_video_service()
            return self._video_service
        else:
            raise Exception("service_manager:add_service(): '{}' service does not exist!".format(s))

    def add_all_services(self):
        for s in ("logging", "monitoring", "video"):
            self.add_service(s)

    def start_service(self, service: Service):
        """
        Starts a service's thread, if the service supports
        threading.
        """
        if not service:
            raise Exception("service_manager:start_service(): Service not added!")

        service.start()
        print("THREAD: {} > Started!".format(service.getName()))

    def start_all_services(self):
        """
        Start all threads.  All must be added first.
        :return:
        """
        for s in (self._monitor_service,
                  self._logging_service,
                  self._video_service):
            self.start_service(s)
        self.all_running = True

    def stop_service(self, service: Service):

        if not service:
            print("SERVICE: service already stopped")

        print("SERVICE: Stopping '{}' ... ".format(service.getName()), end='')
        service.stop()  # signal thread to stop

        if type(service) == MonitorService:
            self._monitor_service = None
        elif type(service) == LoggingService:
            self._logging_service = None
        elif type(service) == VideoService:
            self._video_service = None

        print("STOPPED!")

    def stop_all_services(self):
        """
        Stop all services currently active
        :return:
        """
        self.stop_service(self._monitor_service)
        self.stop_service(self._logging_service)
        self.stop_service(self._video_service)
        self.all_running = False
        print("All threads stopped!")

    def toggle(self, s: str):
        if s == "monitoring" and self._monitor_service:
            self.stop_service(self._monitor_service)
            return
        elif s == "logging" and self._logging_service:
            self.stop_service(self._logging_service)
            return
        elif s == "video" and self._video_service:
            self.stop_service(self._video_service)
            return

        self.add_service(s).start()

    def toggle_all(self):
        if self.all_running:
            # turn all off
            self.stop_all_services()
        else:
            # turn all on
            self.add_all_services()
            self.start_all_services()

    def restart_all(self):
        self.stop_all_services()
        self.add_all_services()
        self.start_all_services()

    def get_queue_size(self):
        return self._video_service.get_queue_size()

    # @staticmethod
    # def _add_detection(detections_queue: queue.Queue, detections: list) -> None:
    #     """add a detection to detections queue. clear an item if queue is full."""
    #     # print("queue_service: adding to detections ...")
    #     print("ADD DETECTION         ", end='\r')
    #     try:
    #         detections_queue.put(detections, block=True, timeout=1 / 60)
    #     except queue.Full:
    #         # if full, remove an item to make room and add new item
    #         _ = detections_queue.get(block=False)  # True, timeout=1 / 60)
    #         detections_queue.task_done()
    #         detections_queue.put(detections)
    #     # print("queue_service: added to detections!")

    # @staticmethod
    # def _add_to_monitor(mon_queue: Queue, t: time, detections: list, f: np.array) -> None:
    #     """add to monitored items queue. monitor thread will determine if
    #     item needs to be monitored or not.  All detections will be put
    #     into this queue."""
    #     print("ADD TO MONITOR       ", end='\r')
    #     d_items = {d.get('name') for d in detections}  # make set of names
    #     # print("queue_service: adding to monitor ...")
    #     try:
    #         mon_queue.put({"t": t, "d": set(d_items), "f": f}, block=True, timeout=1 / 60)
    #     except queue.Full:
    #         # if full, remove an item to make room and add new item
    #         _ = mon_queue.get(block=False)  # True, timeout=1 / 60)
    #         mon_queue.task_done()
    #         mon_queue.put({"t": t, "d": set(d_items), "f": f})
    #     # print("queue_service: added to monitor!")

    # @staticmethod
    # def get_monitored_item(mon_queue: Queue) -> (bool, float, set, np.array):
    #     """return item from monitored items queue"""
    #     print("GET MONITORED ITEM    ", end='\r')
    #     try:
    #         d_elems = mon_queue.get(
    #             block=False)  # block=True, timeout=1 / 60)  # need to allow pass in case of shutdown
    #         # mon_queue.task_done()
    #         time_stamp = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(d_elems.get('t')))
    #
    #         d_items = d_elems.get('d')
    #
    #         return True, time_stamp, d_items, d_elems.get('f')
    #
    #     # except queue.Empty:
    #     except Exception:
    #         return False, None, None, None

    # @staticmethod
    # def get_detections(detections_queue: queue.Queue) -> list:
    #     """get all detections from queue as a list"""
    #     print("GET ALL DETECTIONS   ", end='\r')
    #     det_list = []
    #
    #     while not detections_queue.empty():
    #         det_list.append(detections_queue.get())
    #         detections_queue.task_done()
    #
    #     return det_list
    #
