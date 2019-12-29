from abc import ABC
import numpy as np


class Detector(ABC):
    """
    Abstract class for a detector.
    required methods:
    > detect(frame_num:int, frame:np.array) -> int, np.array
        - returns the frame number and frame with detections
    """

    def detect(self, frame_num: int, frame: np.array) -> (int, np.array, list):
        ...
