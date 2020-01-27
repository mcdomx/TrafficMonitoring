import logging

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
        logger = logging.getLogger('app')
        if detector_name[0] == 'imageai':
            return DetectorImageai(detector_name[0], model_name[0])
        else:
            logger.info("Model not supported: {}/{}".format(detector_name[0], model_name[0]))
