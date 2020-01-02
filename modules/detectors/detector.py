from abc import ABC
import numpy as np


class Detector(ABC):
    """
    Abstract class for a detector.
    required methods:
    > detect(frame_num:int, frame:np.array) -> int, np.array
        - returns the frame number and frame with detections
    """

    def __init__(self, name):
        self.__name = name

    def getName(self):
        return self.__name

    def detect(self, frame_num: int, frame: np.array) -> (int, np.array, list):
        """
        Each supported detector must override this method.
        """
        ...

