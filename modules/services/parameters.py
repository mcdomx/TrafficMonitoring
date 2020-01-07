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

import pafy
import cv2
import numpy as np

from modules.detectors.detector_factory import DetectorFactory


def _read_object_file(file_name) -> set:
    """
    Returns all items in an object file that are set to valid.
    File is a json dict: {<object>:"valid"|"invalid"}
    """
    with open(file_name, 'r') as fp:
        mon_dict = json.load(fp)

    return {k.strip() for k, v in mon_dict.items() if v == 'valid'}


class Params:
    """
    Singleton of all program parameters.
    Some are from environment variables and some are from files.
    """
    singleton = None

    # Access Data in Files
    @staticmethod
    def get_monitored_objects(file_name=os.path.join('.', 'settings', 'monitor_objects.json')) -> set:
        return _read_object_file(file_name)

    @staticmethod
    def get_detected_objects(file_name=os.path.join('.', 'settings', 'detect_objects.json')) -> set:
        return _read_object_file(file_name)

    class __Singleton:
        def __init__(self):
            self._CAM_STREAM = Params._get_cam_name(os.getenv("CAM_STREAM", 0))
            self._CAM_FPS = Params._get_camfps(self._CAM_STREAM)
            self._LOGGING = True if os.getenv("LOGGING", "True") == "True" else False
            self._LOG_FILEPATH = os.getenv("LOG_FILEPATH", os.path.join('.', 'logs', 'files', 'camlogs.txt'))
            self._DETECTION = True if os.getenv("DETECTION", 'True') == "True" else False
            self._DETECTOR_NAME = os.getenv("DETECTOR_NAME", "imageai")
            self._DETECTOR_MODEL = os.getenv("DETECTOR_MODEL", "yolo")
            self._DPM = int(os.getenv("DPM", 20))
            self._DISPLAY_FPS = int(os.getenv("DISPLAY_FPS", 30))
            self._MONITORING = True if os.getenv("MONITORING", "True") == "True" else False
            self._MON_DIR = os.getenv("MON_DIR", os.path.join('.', 'logs', 'images'))
            self._MON_OBJS = Params.get_monitored_objects()
            self._SHOW_VIDEO = True if os.getenv("SHOW_VIDEO", "True") == "True" else False

        @property
        def CAM_STREAM(self):
            return self._CAM_STREAM

        @CAM_STREAM.setter
        def CAM_STREAM(self, val):
            self._CAM_STREAM = Params._get_cam_name(val)

        @property
        def CAM_FPS(self):
            return self._CAM_FPS

        @CAM_FPS.setter
        def CAM_FPS(self, val):
            # ensure that display rate not higher than cam rate
            if val < self._DISPLAY_FPS:
                self._DISPLAY_FPS = val
            self._CAM_FPS = val

        @property
        def LOGGING(self):
            return self._LOGGING

        @LOGGING.setter
        def LOGGING(self, val):
            self._LOGGING = val

        @property
        def LOG_FILEPATH(self):
            return self._LOG_FILEPATH

        @LOG_FILEPATH.setter
        def LOG_FILEPATH(self, val):
            self._LOG_FILEPATH = val

        @property
        def DETECTION(self):
            return self._DETECTION

        @DETECTION.setter
        def DETECTION(self, val):
            self._DETECTION = val


        @property
        def DETECTOR_NAME(self):
            return self._DETECTOR_NAME

        @property
        def DETECTOR_MODEL(self):
            return self._DETECTOR_MODEL

        @property
        def DPM(self):
            return self._DPM

        # @DPM.setter
        # def DPM(self, val):
        #     self._DPM = val

        def update_DPM(self, act_dpm: int):
            if self._DPM > act_dpm and self._DPM > 10:  # throttle down - never go below 10
                self._DPM = act_dpm + int((self._DPM - act_dpm) / 2)
            else:  # throttle up
                self._DPM = act_dpm + 1

        @property
        def DISPLAY_FPS(self):
            return self._DISPLAY_FPS

        @DISPLAY_FPS.setter
        def DISPLAY_FPS(self, val):
            # ensure display rate not higher than cam rate
            if val > self._CAM_FPS:
                self._DISPLAY_FPS = self._CAM_FPS
            else:
                self._DISPLAY_FPS = val

        @property
        def MONITORING(self):
            return self._MONITORING

        @MONITORING.setter
        def MONITORING(self, val):
            self._MONITORING = val

        @property
        def MON_DIR(self):
            return self._MON_DIR

        @MON_DIR.setter
        def MON_DIR(self, val):
            self._MON_DIR = val

        @property
        def MON_OBJS(self):
            return self._MON_OBJS

        @property
        def SHOW_VIDEO(self):
            return self._SHOW_VIDEO

        @SHOW_VIDEO.setter
        def SHOW_VIDEO(self, val):
            self._SHOW_VIDEO = val

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
            rv += "\n\tMONITORED OBJS: {}".format(Params.get_monitored_objects())
            rv += "\n\tSHOW_VIDEO    : {}".format(self.SHOW_VIDEO)

            return rv

    @staticmethod
    def _get_camfps(cam: str) -> float:
        """
        Return the camera's published FPS.
        """
        # cap = cv2.VideoCapture(self.cam)
        cap = cv2.VideoCapture(cam)
        cam_fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        return cam_fps

    @staticmethod
    def __test_cam(cam: str) -> bool:
        cap = cv2.VideoCapture(cam)
        read_pass = cap.grab()
        cap.release()

        if not read_pass:
            return False

        return True

    @staticmethod
    def _get_cam_name(cam: str) -> str:
        """
        Determine the true name of the camera.
        Use YouTube url if not a local webcam.
        """
        # cam = os.getenv("CAM_STREAM", 0)
        # cam = Params.singleton.CAM_STREAM
        if type(cam) is str and cam.isdigit():
            cam = int(cam)

        # test video feed
        read_pass = Params.__test_cam(cam)

        # if capture fails, try as YouTube Stream
        # https://pypi.org/project/pafy/
        if not read_pass:
            if '/' in cam and 'youtube' in cam:  # a full video path was given
                cam = cam.split('/')[-1]
            try:
                videoPafy = pafy.new(cam)
            except:
                raise Exception("No video stream found: {}".format(cam))
            # get most reasonable stream h x w < 350k
            res_limit = 350000
            stream_num = 0

            # use pafy to get the url of the stream
            # find stream with resolution within res_limit
            for i, stream in enumerate(videoPafy.streams):
                x, y = np.array(stream.resolution.split('x'), dtype=int)
                if x * y < res_limit:
                    stream_num = i
                else:
                    break
            stream = videoPafy.streams[stream_num]

            # test stream
            read_pass = Params.__test_cam(stream.url)

            if read_pass:
                cam = stream.url
                print("YouTube Video Stream Detected!")
                print("Video Resolution : {}".format(stream.resolution))

        print("Video Test       : {}".format("OK" if read_pass else "FAIL - check that streamer is publishing"))

        if not read_pass:
            raise Exception("Can't acquire video source: {}".format(cam))
        return cam

    def __new__(cls):
        if Params.singleton is None:
            Params.singleton = Params.__Singleton()

            # if display rate is higher than camera rate, set them to camera fps
            if Params.singleton.DISPLAY_FPS > Params.singleton.CAM_FPS:
                Params.singleton.DISPLAY_FPS = Params.singleton.CAM_FPS

            print(Params.singleton)

        return Params.singleton
