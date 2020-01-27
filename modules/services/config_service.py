"""
Holds and manages global parameters used for
traffic monitoring. Each parameter is expected
to be stored as a local environment variable.

Any methods that determine a variable value
are in this module.  Other modules may change
variable values through accessors only.
"""
import os
import logging
import yaml

import pafy
import cv2
import numpy as np

logger = logging.getLogger('app')


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


# YAML CONFIGURATION
class ConfigYAML(yaml.YAMLObject):
    """

    config_file = os.path.join('.', 'config', 'default.yaml')
    with open(config_file) as fp:
        yaml_data = yaml.load(fp, Loader=yaml.BaseLoader)

    data_dict = ConfigYAML(**yaml_data)

    """
    yaml_tag = u"!StreamYAML"

    def __init__(self, **kwargs):
        if 'CAM_STREAM' in kwargs:
            self._CAM_STREAM = get_cam_name(kwargs['CAM_STREAM'])
        else:
            self._CAM_STREAM = get_cam_name('1EiC9bvVGnk')
        self._CAM_FPS: float = get_camfps(self._CAM_STREAM)

        if 'LOGGING' in kwargs and kwargs['LOGGING'] == 'true':
            self._LOGGING = True
        else:
            self._LOGGING = False
        if 'LOG_FILEPATH' in kwargs:
            self._LOG_FILEPATH = kwargs['LOG_FILEPATH']
        else:
            self._LOG_FILEPATH = os.path.join('.', 'logs', 'files', 'camlogs.txt')
        if 'DETECTION' in kwargs and kwargs['DETECTION'] == 'true':
            self._DETECTION = True
        else:
            self._DETECTION = False
        if 'DETECTOR_NAME' in kwargs:
            self._DETECTOR_NAME = kwargs['DETECTOR_NAME']
        else:
            self._DETECTOR_NAME = 'imageai'

        if 'DETECTOR_MODEL' in kwargs:
            self._DETECTOR_MODEL = kwargs['DETECTOR_MODEL']
        else:
            self._DETECTOR_MODEL = 'yolo'

        if 'DPM' in kwargs:
            self._DPM = float(kwargs['DPM'])
        else:
            self._DPM = 20.0

        if 'DISPLAY_FPS' in kwargs:
            self._DISPLAY_FPS = float(kwargs['DISPLAY_FPS'])
        else:
            self._DISPLAY_FPS = 30.0

        if 'MONITORING' in kwargs and kwargs['MONITORING'] == 'true':
            self._MONITORING = True
        else:
            self._MONITORING = False

        if 'MON_DIR' in kwargs:
            self._MON_DIR = kwargs['MON_DIR']
        else:
            self._MON_DIR = os.path.join('.', 'logs', 'images')

        if 'MON_OBJS' in kwargs:
            self._MON_OBJS = set(kwargs['MON_OBJS'])
        else:
            self._MON_OBJS = set()

        if 'DET_OBJS' in kwargs:
            self._DET_OBJS = set(kwargs['DET_OBJS'])
        else:
            self._DET_OBJS = set()

        if 'BASE_DELAY' in kwargs:
            self._BASE_DELAY = float(kwargs['BASE_DELAY'])
        else:
            self._BASE_DELAY = 0.045

        logger.info(self)

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

    def add_mon_obj(self, obj: str):
        self._MON_OBJS.add(obj)

    def del_mon_obj(self, obj: str):
        self._MON_OBJS.remove(obj)

    def is_monitored(self, obj: str) -> bool:
        if obj in self.MON_OBJS:
            return True
        else:
            return False

    @property
    def DET_OBJS(self) -> set:
        return self._DET_OBJS

    @DET_OBJS.setter
    def DET_OBJS(self, val: set) -> None:
        self._DET_OBJS = val

    def add_det_obj(self, obj: str):
        self._DET_OBJS.add(obj)

    def del_det_obj(self, obj: str):
        self._DET_OBJS.remove(obj)

    def is_detected(self, obj: str) -> bool:
        if obj in self.DET_OBJS:
            return True
        else:
            return False

    @property
    def BASE_DELAY(self) -> float:
        return self._BASE_DELAY

    @BASE_DELAY.setter
    def BASE_DELAY(self, val: float):
        self._BASE_DELAY = max(0.0, val)
    # END GETTERS AND SETTERS ##################################

    def __repr__(self):
        return "%s(\n\tCAM_STREAM=%r, " \
               "\n\tLOGGING=%r, " \
               "\n\tLOG_FILEPATH=%r, " \
               "\n\tDETECTION=%r, " \
               "\n\tDETECTOR_NAME=%r, " \
               "\n\tDETECTOR_MODEL=%r, " \
               "\n\tDPM=%r, " \
               "\n\tDISPLAY_FPS=%r, " \
               "\n\tMONITORING=%r, " \
               "\n\tMON_DIR=%r, " \
               "\n\tMON_OBJS=%r, " \
               "\n\tDET_OBJS=%r, " \
               "\n\tBASE_DELAY=%r)" % (self.__class__.__name__,
                                       self.CAM_STREAM,
                                       self.LOGGING,
                                       self.LOG_FILEPATH,
                                       self.DETECTION,
                                       self.DETECTOR_NAME,
                                       self.DETECTOR_MODEL,
                                       self.DPM,
                                       self.DISPLAY_FPS,
                                       self.MONITORING,
                                       self.MON_DIR,
                                       self.MON_OBJS,
                                       self.DET_OBJS,
                                       self.BASE_DELAY)
