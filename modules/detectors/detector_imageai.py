import os

import numpy as np
import cv2
import json

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
            self.detect_objects = self.get_detected_objects()

        def detect(self, frame: np.array) -> (int, np.array, list):
            """
            Required method of abstract class Detector.
            Arguments include frame number and frame.
            Returns frame_number, detection overlayed frame and detection statistics
            """

            # Perform detection on frame
            det_frame = detections = None
            try:
                if self.detect_objects is None:
                    det_frame, detections = self.detector.detectObjectsFromImage(
                        input_type="array",
                        minimum_percentage_probability=60,
                        input_image=frame,
                        output_type="array",
                        output_image_path='./logs/images/op_image.jpg')
                else:
                    det_frame, detections = self.detector.detectCustomObjectsFromImage(
                        custom_objects=self.detect_objects,
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
                print("detect objects: {}".format(type(self.detect_objects)))
                print("Detector: {}".format(self.detector))
                print("{} // detect(): {}".format(self.DETECTOR_NAME, e))

            return det_frame, detections

        def get_detected_objects(self):
            """
            There are 80 possible objects that you can detect with the
            ObjectDetection class, and they are as seen below.

                person,   bicycle,   car,   motorcycle,   airplane,
                bus,   train,   truck,   boat,   traffic light,   fire hydrant,   stop_sign,
                parking meter,   bench,   bird,   cat,   dog,   horse,   sheep,   cow,   elephant,   bear,   zebra,
                giraffe,   backpack,   umbrella,   handbag,   tie,   suitcase,   frisbee,   skis,   snowboard,
                sports ball,   kite,   baseball bat,   baseball glove,   skateboard,   surfboard,   tennis racket,
                bottle,   wine glass,   cup,   fork,   knife,   spoon,   bowl,   banana,   apple,   sandwich,   orange,
                broccoli,   carrot,   hot dog,   pizza,   donot,   cake,   chair,   couch,   potted plant,   bed,
                dining table,   toilet,   tv,   laptop,   mouse,   remote,   keyboard,   cell phone,   microwave,
                oven,   toaster,   sink,   refrigerator,   book,   clock,   vase,   scissors,   teddy bear,   hair dryer,
                toothbrush.

            To detect only some of the objects above, you will need to call the CustomObjects function and set the name of the
            object(s) you want to detect to through. The rest are False by default.

            https://imageai.readthedocs.io/en/latest/detection/index.html
            Custom objects are defined as 'valid' or 'invalid' in the 'custom_objects.json' file
            Load custom objects file from custom_objects.json' file.
            If file read fails, set all objects to detectable.
            """
            print("loading detected objects ...", end='')

            try:
                with open(os.path.join('.', 'settings', 'detect_objects.json'), 'r') as fp:
                    j = json.load(fp)
                    j = {k: True for k, v in j.items() if v == 'valid'}
                    detect_objects = self.detector.CustomObjects(**j)
                    # detect_objects = json.load(fp)
                print("Loaded detected objects from file!")
            except FileNotFoundError:
                # set all objects to valid if file read doesn't work
                print("No detected_objects.json file found.  Using all objects.")
                detect_objects = self.detector.CustomObjects()
                for k, v in detect_objects.items():
                    detect_objects[k] = 'valid'
            except Exception as e:
                print("Unable to set custom objects: ".format(e))
                return None

            print("{:90}".format(" "), end='\r')  # clear line
            print("Detected objects loaded!")
            return detect_objects

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
