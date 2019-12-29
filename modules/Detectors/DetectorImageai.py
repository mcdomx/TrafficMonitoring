from imageai.Detection import VideoObjectDetection
from imageai.Detection import ObjectDetection
from Detectors import Detector
import os
import numpy as np
import cv2
import json


class Detector_Imageai(Detector):
    """
    Implements Detector abstract class.

    Sets the object detection with the ImageAI implementation (http://imageai.org)
    ref: https://imageai.readthedocs.io/en/latest/detection/index.html
    """
    def __init__(self):
        self.detector = self.get_detector(os.getenv("MODEL", "yolo"), det_type='image')
        self.custom_objects = self.load_custom_objects()

    def detect(self, frame_num: int, frame: np.array) -> (int, np.array, list):
        """
        Required method of Detector.
        Arguments include frame number and frame.
        Returns frame_number, detection overlayed frame and detection statistics
        """
        # Perform detection on frame
        det_frame, detections = self.detector.detectCustomObjectsFromImage(
            custom_objects=self.custom_objects,
            input_type="array",
            minimum_percentage_probability=60,
            input_image=frame,
            output_type="array")

        cv2.putText(det_frame, "{}".format("counting detections.."), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (0, 200, 0), 1)

        return frame_num, det_frame, detections

    def get_detector(self, model_name: str, det_type: str = 'image') -> VideoObjectDetection:
        """
        Returns a ObjectDetection(default) or VideoObjectDetection
        object based on the det_type provided ('image' or 'video').
        Returned object will be loaded and ready to detect.
        """
        print("initializing model ...", end="\r")

        # Setup Detector Object andInference Model
        execution_path = os.getcwd()

        if det_type == 'video':
            detector = VideoObjectDetection()
        else:
            detector = ObjectDetection()

        # Set model path
        if model_name == "tinyyolo":
            detector.setModelTypeAsTinyYOLOv3()
            cur_dir = os.path.join(execution_path, "backbones", "yolo-tiny.h5")
        elif model_name == "retinanet":
            detector.setModelTypeAsRetinaNet()
            cur_dir = os.path.join(execution_path, "backbones", "resnet50_coco_best_v2.0.1.h5")
        else:
            detector.setModelTypeAsYOLOv3()
            cur_dir = os.path.join(execution_path, "backbones", "yolo.h5")
        detector.setModelPath(os.path.join(cur_dir))

        # load model
        detector.loadModel()

        print("{:90}".format(" "), end='\r')  # clear line
        print("'{}' model initialized!".format(model_name))

        return detector

    def load_custom_objects(self) -> dict:
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
        print("loading custom objects ...", end='\r')

        json_file = os.path.join(".", 'custom_objects.json')

        try:
            with open('custom_objects.json', 'r') as fp:
                custom_objects = json.load(fp)
        except:
            # set all objects to valid if file read doesn't work
            custom_objects = self.detector.CustomObjects()
            for k, v in custom_objects.items():
                custom_objects[k] = 'valid'

        print("{:90}".format(" "), end='\r')  # clear line
        print("custom objects loaded!")

        return custom_objects
