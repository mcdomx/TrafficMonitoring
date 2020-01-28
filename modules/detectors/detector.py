from abc import ABC, abstractmethod
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

    @abstractmethod
    def detect(self, frame: np.array, det_objs: set) -> (int, np.array, list):
        """
        Each supported detector must override this method.
        :frame: np.array) - frame from which to detect objects
        :det_objs: set - set of object names which should be detected
        Returns frame number, frame and detections
        """
        ...

    @abstractmethod
    def get_trained_objects(self) -> set:
        """
        Each supported detector must override this method.
        :return: set of strings where each string is the name of a trained object. Spaces
        must be represented with an underscore, '_'.
        """
        ...
