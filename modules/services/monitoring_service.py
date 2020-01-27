import os
import numpy as np
import time

import cv2

from modules.services.service import Service


class MonitorService(Service):
    """
    This service will determine if a detection includes items that should
    be monitored and will save the respective image in the specified
    directory.  Since this is only done for each detection, this does
    not need to be a running thread and can be called after each
    detection.

    The objects monitored and stored location can be changed using attribute
    setters.

    """
    def __init__(self, name, detection_rate: float, objects: set, dir_path: str):
        Service.__init__(self, name)
        self._dpm = detection_rate
        self._mon_objs = objects
        self._mon_dir = dir_path

    # GETTERS AND SETTERS ####################
    @property
    def dpm(self):
        return self._dpm

    @dpm.setter
    def dpm(self, val):
        self._dpm = val

    @property
    def mon_objs(self):
        return self._mon_objs

    @mon_objs.setter
    def mon_objs(self, val):
        self._mon_objs = val

    @property
    def mon_dir(self):
        return self._mon_dir

    @mon_dir.setter
    def mon_dir(self, val):
        self._mon_dir = val

    # END GETTERS AND SETTERS ####################

    def start(self):
        self._running = True

    def evaluate(self, image: np.array, detections: list, frame_time: time):
        """
        Evaluates the list of detected items and saves the image if the
        image includes detections that should  be monitored.
        :param image: image that includes the detected items in 'detections' list
        :param detections: list of detections in corresponding image
        :param frame_time: time that corresponding image was captured
        :return: None
        """
        time_stamp = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(frame_time))

        # get unique name values of detected items
        d_items = {d.get('name') for d in detections}

        # if any detected items are in the monitored objects, save image
        if d_items & self.mon_objs:
            cv2.imwrite(os.path.join(self.mon_dir, "{}.png".format(time_stamp)), image)
