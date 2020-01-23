"""
Holds and manages global parameters used for
traffic monitoring. Each parameter is expected
to be stored as a local environment variable.

Any methods that determine a variable value
are in this module.  Other modules may change
variable values through accessors only.
"""
import os
import json
import logging

import pafy
import cv2
import numpy as np

logger = logging.getLogger('app')


# Access Data in Files
def __read_object_file(file_name) -> dict:
    """
    Returns all items in an object file and their validity.
    Valid objects are being monitored.
    File is a json dict: {<object>:"valid"|"invalid"}
    """
    with open(file_name, 'r') as fp:
        all_objects = json.load(fp)
    return all_objects


def get_monitored_objects(file_name=os.path.join('.', 'settings', 'monitor_objects.json')) -> set:
    all_objects = __read_object_file(file_name)
    return {k.strip() for k, v in all_objects.items() if v == 'valid'}


def get_monitored_objects_all(file_name=os.path.join('.', 'settings', 'monitor_objects.json')) -> dict:
    return __read_object_file(file_name)


def get_detected_objects(file_name=os.path.join('.', 'settings', 'detect_objects.json')) -> set:
    all_objects = __read_object_file(file_name)
    return {k.strip() for k, v in all_objects.items() if v == 'valid'}


def get_detected_objects_all(file_name=os.path.join('.', 'settings', 'detect_objects.json')) -> dict:
    return __read_object_file(file_name)


# END FILE ACCESS FUNCTIONS


# CAMERA FUNCTIONS
def get_cam_name(cam: str) -> str:
    """
    Determine the true name of the camera.
    Use YouTube url if not a local webcam.
    """

    if type(cam) is str and cam.isdigit():
        cam = int(cam)

    # test video feed
    read_pass = _test_cam(cam)

    # if capture fails, try as YouTube Stream
    # https://pypi.org/project/pafy/
    if not read_pass:
        if '/' in cam and 'youtube' in cam:  # a full video path was given
            cam = cam.split('/')[-1]
        try:
            video_pafy = pafy.new(cam)
        except Exception:
            raise Exception("No video stream found: {}".format(cam))
        # get most reasonable stream h x w < 350k
        res_limit = 350000
        stream_num = 0

        # use pafy to get the url of the stream
        # find stream with resolution within res_limit
        for i, stream in enumerate(video_pafy.streams):
            x, y = np.array(stream.resolution.split('x'), dtype=int)
            if x * y < res_limit:
                stream_num = i
            else:
                break
        stream = video_pafy.streams[stream_num]

        # test stream
        read_pass = _test_cam(stream.url)

        if read_pass:
            cam = stream.url
            logger.info("YouTube Video Stream Detected!")
            logger.info("Video Resolution : {}".format(stream.resolution))

    logger.info("Video Test       : {}".format("OK" if read_pass else "FAIL - check that streamer is publishing"))

    if not read_pass:
        raise Exception("Can't acquire video source: {}".format(cam))

    return cam


def _test_cam(cam: str) -> bool:
    cap = cv2.VideoCapture(cam)
    read_pass = cap.grab()
    cap.release()

    if not read_pass:
        return False

    return True


def get_camfps(cam: str) -> float:
    """
    Return the camera's published FPS.
    """
    cap = cv2.VideoCapture(cam)
    cam_fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    return cam_fps

# END CAMERA FUNCTIONS ##########################


class Config(object):
    """
    Holds video streaming and detection parameters.
    Defaults are from environment variables and some are from files.
    Where environment variables are not set, default values are provided.
    """
    def __init__(self):
        self._CAM_STREAM: str = get_cam_name(os.getenv("CAM_STREAM", 0))
        self._CAM_FPS: float = get_camfps(self.CAM_STREAM)
        self._LOGGING: bool = True if os.getenv("LOGGING", "True") == "True" else False
        self._LOG_FILEPATH: str = os.getenv("LOG_FILEPATH", os.path.join('.', 'logs', 'files', 'camlogs.txt'))
        self._DETECTION: bool = True if os.getenv("DETECTION", 'True') == "True" else False
        self._DETECTOR_NAME: str = os.getenv("DETECTOR_NAME", "imageai")
        self._DETECTOR_MODEL: str = os.getenv("DETECTOR_MODEL", "yolo")
        self._DPM: float = int(os.getenv("DPM", 20))
        self._DISPLAY_FPS: float = int(os.getenv("DISPLAY_FPS", 30))
        self._MONITORING: bool = True if os.getenv("MONITORING", "True") == "True" else False
        self._MON_DIR: str = os.getenv("MON_DIR", os.path.join('.', 'logs', 'images'))
        self._MON_OBJS: set = get_monitored_objects()
        self._MON_OBJS_ALL: dict = get_monitored_objects_all()
        self._DET_OBJS: set = get_detected_objects()
        self._DET_OBJS_ALL: dict = get_detected_objects_all()
        self._SHOW_VIDEO: bool = True if os.getenv("SHOW_VIDEO", "True") == "True" else False
        self._BASE_DELAY: float = 0.000

        logger.info("Parameter Service Established")

    def __str__(self):
        rv = "TRAFFIC DETECTION PARAMETERS:\n"
        rv += "\n\tCAM_STREAM    : {}".format(self.CAM_STREAM)
        rv += "\n\tCAM_FPS       : {}".format(self.CAM_FPS)
        rv += "\n\tLOGGING       : {}".format(self.LOGGING)
        rv += "\n\tLOG_FILEPATH  : {}".format(self.LOG_FILEPATH)
        rv += "\n\tDETECTION     : {}".format(self.DETECTION)
        rv += "\n\tDETECTOR      : {}".format(self.DETECTOR_NAME)
        rv += "\n\tMODEL         : {}".format(self.DETECTOR_MODEL)
        rv += "\n\tDPM           : {}".format(self.DPM)
        rv += "\n\tDISPLAY_FPS   : {}".format(self.DISPLAY_FPS)
        rv += "\n\tMONITORING    : {}".format(self.MONITORING)
        rv += "\n\tMONITORED OBJS: {}".format(self.MON_OBJS)
        rv += "\n\tSHOW_VIDEO    : {}".format(self.SHOW_VIDEO)
        rv += "\n\tBASE_DELAY    : {}".format(self.BASE_DELAY)

        return rv

    # PARAMETER GETTERS AND SETTERS ##################################
    @property
    def CAM_STREAM(self):
        return self._CAM_STREAM

    @CAM_STREAM.setter
    def CAM_STREAM(self, val):
        self._CAM_STREAM = get_cam_name(val)

    @property
    def CAM_FPS(self):
        """Get cam's local program set FPS"""
        return self._CAM_FPS

    @CAM_FPS.setter
    def CAM_FPS(self, val):
        """Set cam's local program FPS when published rate is not accurate"""
        # ensure that display rate not higher than cam rate
        if val < self._DISPLAY_FPS:
            self._DISPLAY_FPS = val
        self._CAM_FPS = val

    @property
    def LOGGING(self) -> bool:
        return self._LOGGING

    @LOGGING.setter
    def LOGGING(self, val: bool) -> None:
        self._LOGGING = val

    @property
    def LOG_FILEPATH(self) -> str:
        return self._LOG_FILEPATH

    @LOG_FILEPATH.setter
    def LOG_FILEPATH(self, val: str) -> None:
        self._LOG_FILEPATH = val

    @property
    def DETECTION(self) -> bool:
        return self._DETECTION

    @DETECTION.setter
    def DETECTION(self, val: bool) -> None:
        self._DETECTION = val

    @property
    def DETECTOR_NAME(self) -> str:
        return self._DETECTOR_NAME

    @DETECTOR_NAME.setter
    def DETECTOR_NAME(self, val: str) -> None:
        self._DETECTOR_NAME = val

    @property
    def DETECTOR_MODEL(self) -> str:
        return self._DETECTOR_MODEL

    @DETECTOR_MODEL.setter
    def DETECTOR_MODEL(self, val: str) -> None:
        self._DETECTOR_MODEL = val

    @property
    def DPM(self) -> float:
        return self._DPM

    @DPM.setter
    def DPM(self, val: float):
        """ Throttle up or down. Never go below 10 DPM."""
        if self._DPM > val and self._DPM > 10:
            self._DPM = val + int((self._DPM - val) / 2)
        else:  # throttle up
            self._DPM = val + 1

    @property
    def DISPLAY_FPS(self) -> float:
        return self._DISPLAY_FPS

    @DISPLAY_FPS.setter
    def DISPLAY_FPS(self, val: float) -> None:
        """Ensures that the display rate is not higher than cam rate"""
        if val > self._CAM_FPS:
            self._DISPLAY_FPS = self._CAM_FPS
        else:
            self._DISPLAY_FPS = val

    @property
    def MONITORING(self) -> bool:
        return self._MONITORING

    @MONITORING.setter
    def MONITORING(self, val: bool):
        self._MONITORING = val

    @property
    def MON_DIR(self) -> str:
        return self._MON_DIR

    @MON_DIR.setter
    def MON_DIR(self, val: str) -> None:
        self._MON_DIR = val

    @property
    def MON_OBJS(self) -> set:
        return self._MON_OBJS

    @MON_OBJS.setter
    def MON_OBJS(self, val: set) -> None:
        self._MON_OBJS = val

    @property
    def MON_OBJS_ALL(self) -> dict:
        return self._MON_OBJS_ALL

    @MON_OBJS_ALL.setter
    def MON_OBJS_ALL(self, val: dict) -> None:
        self._MON_OBJS_ALL = val

    @property
    def DET_OBJS(self) -> set:
        return self._DET_OBJS

    @DET_OBJS.setter
    def DET_OBJS(self, val: set) -> None:
        self._DET_OBJS = val

    @property
    def DET_OBJS_ALL(self) -> dict:
        return self._DET_OBJS_ALL

    @DET_OBJS_ALL.setter
    def DET_OBJS_ALL(self, val: dict) -> None:
        self._DET_OBJS_ALL = val

    @property
    def SHOW_VIDEO(self) -> bool:
        return self._SHOW_VIDEO

    @SHOW_VIDEO.setter
    def SHOW_VIDEO(self, val: bool):
        self._SHOW_VIDEO = val

    @property
    def BASE_DELAY(self) -> float:
        return self._BASE_DELAY

    @BASE_DELAY.setter
    def BASE_DELAY(self, val: float):
        self._BASE_DELAY = max(0.0, val)

    # END GETTERS AND SETTERS ##################################
