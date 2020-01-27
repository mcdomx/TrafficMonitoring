import logging
import numpy as np
import os
import yaml
from multiprocessing import Process

from flask_socketio import SocketIO

from modules.services.monitoring_service import MonitorService
from modules.services.logging_service import LoggingService
from modules.services.video_service import VideoService
from modules.services.service import Service
from modules.services.config_service import ConfigYAML

logger = logging.getLogger('app')


class ServiceManager(object):
    """
    Handles starting and stopping all required services.
    Acts as interface to underlying services.
    """
    def __init__(self, socketio: SocketIO, config_file: os.path = None):

        with open(config_file) as fp:
            yaml_data = yaml.load(fp, Loader=yaml.BaseLoader)

        self.all_running = False
        self.socketio = socketio
        self._config = ConfigYAML(**yaml_data)
        self._monitor_service: MonitorService = self.get_monitor_service()
        self._logging_service: LoggingService = self.get_logging_service()
        self._video_service: VideoService = self.get_video_service()

    def get_frame(self) -> (bool, np.array):
        success, image, detections, frame_time = self._video_service.get_next_frame()

        if not success:
            return False, None

        if detections:

            if self._logging_service:
                self._logging_service.log_detections(detections)

            if self._monitor_service:
                # self._monitor_service.evaluate(image, detections, frame_time)
                p_mon = Process(target=self._monitor_service.evaluate,
                                kwargs={'image': image,
                                        'detections': detections,
                                        'frame_time': frame_time})
                p_mon.start()
                p_mon.join()

        return True, image

    def get_monitor_service(self, name=None, detection_rate=None, objects=None, dir_path=None):
        if not name:
            name = "monitor-service"
        if not detection_rate:
            detection_rate = self._config.DPM
        if not objects:
            objects = self._config.MON_OBJS
        if not dir_path:
            dir_path = self._config.MON_DIR
        # print("SERVICE: Adding '{}'".format(name))
        return MonitorService(name=name,
                              detection_rate=detection_rate,
                              objects=objects,
                              dir_path=dir_path)

    def get_logging_service(self,
                            name=None,
                            detection_rate=None,
                            file_path=None,
                            socketio=None):
        if not name:
            name = "logging-service"
        if not detection_rate:
            detection_rate = self._config.DPM
        if not file_path:
            file_path = self._config.LOG_FILEPATH
        if not socketio:
            socketio = self.socketio

        return LoggingService(name=name,
                              detection_rate=detection_rate,
                              file_path=file_path,
                              socketio=socketio)

    def get_video_service(self, name=None,
                          detector_name=None,
                          detector_model=None,
                          base_delay=None,
                          cam_rate=None,
                          stream=None,
                          display_rate=None,
                          detection_rate=None,
                          detected_objects=None):
        if not name:
            name = "video-service"
        if not detector_name:
            detector_name = self._config.DETECTOR_NAME,
        if not detector_model:
            detector_model = self._config.DETECTOR_MODEL,
        if not base_delay:
            base_delay = self._config.BASE_DELAY,
        if not cam_rate:
            cam_rate = self._config.CAM_FPS,
        if not stream:
            stream = self._config.CAM_STREAM,
        if not display_rate:
            display_rate = self._config.DISPLAY_FPS,
        if not detection_rate:
            detection_rate = self._config.DPM
        if not detected_objects:
            detected_objects = self.get_detected_objects()
        # print("SERVICE: Adding '{}'".format(name))
        return VideoService(name=name,
                            detector_name=detector_name,
                            detector_model=detector_model,
                            base_delay=base_delay,
                            cam_rate=cam_rate,
                            stream=stream,
                            display_rate=display_rate,
                            detection_rate=detection_rate,
                            detected_objects=detected_objects)

    def add_service(self, s: str) -> Service:

        if s == "monitor":
            added_service = self._monitor_service = self.get_monitor_service()
            # return self._monitor_service
        elif s == "log":
            added_service = self._logging_service = self.get_logging_service()
            # return self._logging_service
        elif s == "video":
            added_service = self._video_service = self.get_video_service()
            # return self._video_service
        else:
            raise Exception("service_manager:add_service(): '{}' service does not exist!".format(s))

        logger.info("SERVICE: Adding '{}'".format(s))
        return added_service

    def add_all_services(self):
        for s in ("log", "monitor", "video"):
            self.add_service(s)

    def start_service(self, s):
        """
        Starts a service's thread, if the service supports
        threading.
        """
        if type(s) == str:
            if s == "monitor":
                self._monitor_service.start()
            elif s == "log":
                self._logging_service.start()
            elif s == "video":
                self._video_service.start()

        elif type(s) == MonitorService:
            self._monitor_service.start()
        elif type(s) == LoggingService:
            self._logging_service.start()
        elif type(s) == VideoService:
            self._video_service.start()
        else:
            raise Exception("SERVICE: {} > Not Recognized - Nothing started!!".format(s.getName()))

        logger.info("SERVICE: {} > Started!".format(s.getName()))

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

    def stop_service(self, s):

        def kill(x):

            if not x:
                logger.warning("SERVICE: '{}' was not running.")
                return

            x.stop()  # signal service to stop
            logger.info("SERVICE: Stopped '{}'".format(x.getName()))
            del x  # delete service object

        if type(s) == str:
            if s == "monitor":
                kill(self._monitor_service)
                self._monitor_service = None
            elif s == "log":
                kill(self._logging_service)
                self._logging_service = None
            elif s == "video":
                kill(self._video_service)
                self._video_service = None
        elif type(s) == MonitorService:
            kill(self._monitor_service)
            self._monitor_service = None
        elif type(s) == LoggingService:
            kill(self._logging_service)
            self._logging_service = None
        elif type(s) == VideoService:
            kill(self._video_service)
            self._video_service = None

        else:
            raise Exception("service_manager:stop_service(): '{}' service does not exist!".format(s))

    def stop_all_services(self):
        """
        Stop all services currently active
        :return: None
        """
        if self._monitor_service:
            self.stop_service(self._monitor_service)
        if self._logging_service:
            self.stop_service(self._logging_service)
        if self._video_service:
            self.stop_service(self._video_service)

        self.all_running = False
        logger.info("All threads stopped!")

    def toggle(self, s: str):
        if s == "monitor" and self._monitor_service:
            self.stop_service(self._monitor_service)
            return
        elif s == "log" and self._logging_service:
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

    def get_trained_objects(self) -> set:
        return self._video_service.get_trained_objects()

    def add_mon_obj(self, obj: str):
        self._config.add_mon_obj(obj)

    def del_mon_obj(self, obj: str):
        self._config.del_mon_obj(obj)

    def is_monitored(self, obj: str) -> bool:
        return self._config.is_monitored(obj)

    def get_monitored_objects(self) -> set:
        return self._config.MON_OBJS

    def add_det_obj(self, obj: str):
        self._config.add_det_obj(obj)
        self._video_service.det_objs = self._config.DET_OBJS

    def del_det_obj(self, obj: str):
        self._config.del_det_obj(obj)
        self._video_service.det_objs = self._config.DET_OBJS

    def is_detected(self, obj: str) -> bool:
        return self._config.is_detected(obj)

    def get_detected_objects(self) -> set:
        return self._config.DET_OBJS

    @property
    def base_delay(self) -> float:
        return self._config.BASE_DELAY

    @base_delay.setter
    def base_delay(self, val: float):
        self._config.BASE_DELAY = val

