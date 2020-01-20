from modules.detectors.detector import Detector
from modules.detectors.detector_imageai import DetectorImageai


class DetectorFactory:

    @staticmethod
    def get(detector_name: str, model_name: str) -> Detector:
        """
        Returns Detector object.
        Update this function to add new detection models.
        New models will require new class that inherits from Detector class.
        """

        if detector_name == 'imageai':
            d = DetectorImageai(detector_name, model_name)
            print(d)
            return d
