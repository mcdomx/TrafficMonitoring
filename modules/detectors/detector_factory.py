from modules.detectors.detector import Detector
from modules.detectors.detector_imageai import DetectorImageai
from modules.services.parameters import Params

p = Params()


class DetectorFactory:

    @staticmethod
    def get() -> Detector:
        """
        Returns uninitialized Detector object.
        Update this function to add new detection models.
        New models will require new class that inherits from Detector class.
        """
        det = p.DETECTOR

        if det == 'imageai':
            return DetectorImageai()
