from abc import ABC
import numpy as np


class Detector(ABC):
    """
    Abstract class for a detector.
    required methods:
    > detect(frame_num:int, frame:np.array) -> int, np.array
        - returns the frame number and frame with detections
    """

    def __init__(self, detector_name: str, model_name: str):
        self._detector_name = detector_name
        self._model_name = model_name

    def __str__(self):
        return "Detector: {} // {}".format(self.DETECTOR_NAME, self.MODEL_NAME)

    @property
    def DETECTOR_NAME(self):
        return self._detector_name

    @property
    def MODEL_NAME(self):
        return self._model_name

    def detect(self, frame: np.array) -> (int, np.array, list):
        """
        Each supported detector must override this method.
        Returns frame number, frame and detections
        """
        ...

    def get_trained_objects(self) -> set:
        """
        Each supported detector must override this method.
        :return: set of strings where each string is the name of a trained object
        """
        ...
