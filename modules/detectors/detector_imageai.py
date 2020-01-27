import os

import numpy as np
import cv2
# import json

import imageai.Detection
from modules.detectors.detector import Detector


class DetectorImageai:
    """
    Implements Detector abstract class.

    Sets the object detection with the ImageAI implementation (http://imageai.org)
    ref: https://imageai.readthedocs.io/en/latest/detection/index.html
    """

    singleton = None

    def __new__(cls, detector_name, model_name):
        if cls.singleton is None:
            cls.singleton = cls.__Singleton(detector_name, model_name)
        return cls.singleton

    class __Singleton(Detector):
        def __init__(self, detector_name, model_name):
            Detector.__init__(self, detector_name, model_name)
            self.detector = self.get_detector(det_type='image')
            # self.detect_objects = self.get_detected_objects()

        def detect(self, frame: np.array, det_objs: set = None) -> (int, np.array, list):
            """
            Required method of abstract class Detector.
            Arguments include frame number and frame.
            Returns frame_number, detection overlayed frame and detection list
            """

            # Perform detection on frame
            det_frame = detections = None
            try:
                if det_objs is None:
                    det_frame, detections = self.detector.detectObjectsFromImage(
                        input_type="array",
                        minimum_percentage_probability=60,
                        input_image=frame,
                        output_type="array",
                        output_image_path='./logs/images/op_image.jpg')
                else:
                    objs = self.detector.CustomObjects()
                    for o in det_objs:
                        objs[o] = 'valid'

                    det_frame, detections = self.detector.detectCustomObjectsFromImage(
                        custom_objects=objs,
                        input_type="array",
                        minimum_percentage_probability=60,
                        input_image=frame,
                        output_type="array",
                        output_image_path='./logs/images/op_image.jpg')

                cv2.putText(det_frame,
                            "{}".format("counting detections.."),
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.4,
                            (0, 0, 200),
                            1)

            except Exception as e:
                print("frame shape: {}".format(frame.shape))
                print("detect objects: {}".format(type(det_objs)))
                print("Detector: {}".format(self.detector))
                print("{} // detect(): {}".format(self.DETECTOR_NAME, e))

            return det_frame, detections

        def get_trained_objects(self) -> set:
            model_objects = self.detector.CustomObjects()
            model_objects = {o.replace(' ', '_') for o in model_objects.keys()}
            return model_objects

        def get_detector(self, det_type: str = 'image'):
            """
            Returns a ObjectDetection(default) or VideoObjectDetection
            object based on the det_type provided ('image' or 'video').
            Returned object will be loaded and ready to detect.
            """
            print("initializing model ...", end="\r")

            # Setup Detector Object andInference Model
            execution_path = os.getcwd()

            if det_type == 'video':
                detector = imageai.Detection.VideoObjectDetection()
            else:
                detector = imageai.Detection.ObjectDetection()

            # Set model path
            if self.MODEL_NAME == "tinyyolo":
                detector.setModelTypeAsTinyYOLOv3()
                cur_dir = os.path.join(execution_path, "backbones", "yolo-tiny.h5")
            elif self.MODEL_NAME == "retinanet":
                detector.setModelTypeAsRetinaNet()
                cur_dir = os.path.join(execution_path, "backbones", "resnet50_coco_best_v2.0.1.h5")
            else:
                detector.setModelTypeAsYOLOv3()
                cur_dir = os.path.join(execution_path, "backbones", "yolo.h5")
            detector.setModelPath(os.path.join(cur_dir))

            # load model
            detector.loadModel()

            print("{:90}".format(" "), end='\r')  # clear line
            print("'{}' model initialized!".format(self.MODEL_NAME))

            return detector


