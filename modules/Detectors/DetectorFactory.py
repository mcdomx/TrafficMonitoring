import os
from modules.Detectors.Detector import Detector
from modules.Detectors.DetectorImageai import DetectorImageai


class DetectorFactory():

    @staticmethod
    def get() -> Detector:
        """
        Returns uninitialized Detector object.
        Update this function to add new detection models.
        New models will require new class that inherits from Detector class.
        """
        det = os.getenv("DETECTOR", "imageai")

        if det == 'imageai':
            return DetectorImageai()
