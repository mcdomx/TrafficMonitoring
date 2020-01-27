import cv2
import numpy as np
import threading
import queue
import time
import logging
from collections import namedtuple

from modules.detectors.detector_factory import DetectorFactory
from modules.detectors.detector import Detector
from modules.timers.elapsed_time import ElapsedTime
from modules.services.service import Service

logger = logging.getLogger('app')

Frame = namedtuple("Frame", ['num', 'time', 'image', 'queue', 'detections'])


def _get_detector(name, model) -> Detector:
    d = DetectorFactory.get(name, model)
    logger.info("RETURNING MODEL: {}".format(d))
    return d


def add_overlay(frame: np.array, stats: dict) -> np.array:
    """
    Adds overly to current 'frame'.  Uses local variables
    stats and frame.  'stats' is a dictionary
    where keys are displayed statistics and values are the
    respective values.
    """
    # HELP MENU
    cv2.putText(frame, "{}".format("'q' - quit"),
                (10, frame.shape[0] - 10),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.4,
                color=(200, 0, 0),
                thickness=1)

    # STATISTICS
    # cv2.putText(frame, "{}".format("dpm: {}".format(round(capture_thread.get_dpm(), 1))),
    for i, (k, v) in enumerate(stats.items()):
        cv2.putText(frame, "{:14} : {}".format(k, round(v, 3)),
                    (frame.shape[1] - 180, frame.shape[0] - 10 - (i * 15)),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.4,
                    color=(200, 0, 0),
                    thickness=1)

    return frame


class VideoService(Service, threading.Thread):
    """
    Thread that will read images from video stream.
    Places frames in queues depending on whether or not
    object detection was performed on the frame or not.
    Arguments are references to the queues where frames
    are put into.
    """
    def __init__(self,
                 name: str,
                 detector_name: str,
                 detector_model: str,
                 stream: str,
                 cam_rate: float,
                 display_rate: float,
                 detection_rate: float,
                 base_delay: float,
                 buffer_size: int = 256,
                 detected_objects: set = None):
        Service.__init__(self, name)
        threading.Thread.__init__(self)
        self.setName(name)
        self._elapsed_time = None
        self._detector_name = detector_name
        self._detector_model = detector_model
        self._detector = _get_detector(detector_name, detector_model)
        self._cam_stream = stream
        self._cam_fps = cam_rate
        self._display_fps = display_rate
        self._dpm = detection_rate
        self._base_delay = base_delay
        self._det_objs = detected_objects

        # queues
        self.buffer_size = buffer_size
        self._ref_queue = queue.Queue(buffer_size)  # includes frame num and queue to get frame from
        self._det_queue = queue.Queue(buffer_size)  # includes frames with processed detections
        self._undet_queue = queue.Queue(buffer_size)  # includes frame without detections

    # GETTERS AND SETTERS

    @property
    def det_name(self) -> str:
        return self._detector_name[0]

    @det_name.setter
    def det_name(self, val: str):
        self._detector_name = val

    @property
    def det_model(self) -> str:
        return self._detector_model[0]

    @det_model.setter
    def det_model(self, val: str):
        self._detector_model = val

    @property
    def cam_stream(self) -> str:
        return self._cam_stream[0]

    @cam_stream.setter
    def cam_stream(self, val: str):
        self._cam_stream = val

    @property
    def cam_fps(self) -> float:
        return self._cam_fps[0]

    @cam_fps.setter
    def cam_fps(self, val: float):
        self._cam_fps = val

    @property
    def display_fps(self) -> float:
        return self._display_fps[0]

    @display_fps.setter
    def display_fps(self, val: float):
        self._display_fps = val

    @property
    def dpm(self) -> float:
        return self._dpm

    @dpm.setter
    def dpm(self, val: float):
        self._dpm = val

    @property
    def base_delay(self) -> float:
        return self._base_delay[0]

    @base_delay.setter
    def base_delay(self, val: float):
        self._base_delay = val

    @property
    def det_objs(self) -> set:
        return self._det_objs

    @det_objs.setter
    def det_objs(self, objs: set):
        self._det_objs = objs

    def add_det_obj(self, obj: str):
        self._det_objs.add(obj)

    def del_det_obj(self, obj: str):
        self._det_objs.remove(obj)


    # END GETTERS AND SETTERS

    def get_trained_objects(self) -> set:
        return self._detector.get_trained_objects()

    def start(self):
        self._running = True
        threading.Thread.start(self)

    def get_queue_size(self) -> int:
        return self._ref_queue.qsize()

    def add_frame(self, frame: Frame,) -> None:

        print("ADD FRAME              ", end='\r')

        try:
            self._ref_queue.put((frame.num, frame.queue), block=True)  # True, timeout=1 / 60)
            frame.queue.put(frame, block=True)  # True, timeout=1 / 60)

        except queue.Full:
            pass

    def get_next_frame(self) -> (bool, np.array, list, float):
        """
        Return the next frame image and associated
        detections, if they exist.
        :return: frame image, list of detections
        """
        frame_num, frame_queue = self._ref_queue.get()
        try:
            frame = frame_queue.get(block=False)
        except queue.Empty:
            return False, None, None, None

        return True, frame.image, frame.detections, frame.time

    def run(self):
        """
        Thread stops when capture is closed.
        """
        # get detector
        # detector = DetectorFactory.get(self.det_name, self.det_model)
        # logger.info("Loaded detector->  {}".format(detector))
        detector = self._detector

        # initialize loop variables
        frame_num = 0

        # open cam and start capture
        logger.info("Starting cam ... ")
        cap = cv2.VideoCapture(self.cam_stream)

        # main loop
        self._running = True
        if self._running and cap.isOpened():
            logger.info("\tCAM STARTED!")

        # start timer
        self._elapsed_time = ElapsedTime()
        last_detection_time = 0

        while cap.isOpened() and self._running:

            # loop until display fps reached
            c = 0
            while c < self.cam_fps / self.display_fps:
                c += int(cap.grab())

            # get next cam frame
            cur_frame = None
            while cur_frame is None:
                _, cur_frame = cap.read()
            last_pull_time = self._elapsed_time.get()
            frame_num += 1

            stats = {'dpm': round(self.dpm, 1),
                     'delay': round(self.base_delay, 3),
                     'buffer_size': self._ref_queue.qsize(),
                     'elapsed_time': self._elapsed_time}

            q = self._undet_queue
            detections = None
            frame = cur_frame.copy()

            # if detection/inference is on, perform detections at detection rate
            if last_pull_time - last_detection_time >= 60 / self.dpm:

                last_detection_time = last_pull_time

                try:
                    # run detection on frame
                    frame, detections = detector.detect(frame=cur_frame.copy(), det_objs=self.det_objs)
                    q = self._det_queue

                except Exception as e:
                    logger.error("{} // run() DETECTION: {}".format(self.getName(), e))

            print("ADD OVERLAY         ", end='\r')
            frame = add_overlay(frame, stats)

            frame_tup = Frame(frame_num, time.time(), frame, q, detections)

            self.add_frame(frame=frame_tup)

        # release camera upon exit
        cap.release()
