import threading
import queue
import cv2
import time
import os
import pafy
import numpy as np

from modules.Detectors.DetectorFactory import DetectorFactory
from modules.Detectors.Detector import Detector
from modules.Detectors.DetectorImageai import DetectorImageai


class VideoCaptureThread(threading.Thread):
    """
    Thread that will read images from video stream.
    Places frames in queues depending on whether or not
    object detection was performed on the frame or not.
    Arguments are references to the queues where frames
    are put into.
    """
    @staticmethod
    def __get_object_detector() -> Detector:
        """
        Returns uninitialized Detector object.
        Update this function to add new detection models.
        New models will require new class that inherits from Detector class.
        """
        det = os.getenv("DETECTOR", "imageai")

        if det == 'imageai':
            return DetectorImageai()

    @staticmethod
    def __test_cam(cam: str) -> bool:
        cap = cv2.VideoCapture(cam)
        read_pass = cap.grab()
        cap.release()

        if not read_pass:
            return False

        return True

    def __init__(self,
                 ref_queue: queue.Queue,
                 det_queue: queue.Queue,
                 undet_queue: queue.Queue,
                 detections_queue: queue.Queue,
                 mon_queue: queue.Queue,
                 dpm=20,
                 display_fps=30):
        threading.Thread.__init__(self)
        self.ref_queue = ref_queue
        self.det_queue = det_queue
        self.undet_queue = undet_queue
        self.detections_queue = detections_queue
        self.running = False
        self.dpm = dpm                  # detections per minute
        self.display_fps = display_fps  # local display fps
        self.start_time = None
        self.detection_on = True if os.getenv("DETECTION", 'True') == "True" else False
        self.cam = self.__set_cam_name()
        self.cam_fps = self.get_camfps()
        self.mon_queue = mon_queue

        # If camera rate is lower that the display rate,
        # set the display_rate equal to camera_rate
        if self.display_fps > self.cam_fps:
            self.display_fps = self.cam_fps

    def get_camfps(self) -> float:
        """
        Return the camera's published FPS.
        """
        cap = cv2.VideoCapture(self.cam)
        cam_fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        return cam_fps

    def __set_cam_name(self) -> str:
        """
        Determine the true name of the camera.
        Use YouTube url if not a local webcam.
        """
        cam = os.getenv("CAM_STREAM", 0)
        if cam.isdigit():
            cam = int(cam)

        # test video feed
        read_pass = self.__class__.__test_cam(cam)

        # if capture fails, try as YouTube Stream
        # https://pypi.org/project/pafy/
        if not read_pass:
            if '/' in cam and 'youtube' in cam:  # a full video path was given
                cam = cam.split('/')[-1]
            try:
                videoPafy = pafy.new(cam)
            except:
                raise Exception("No video stream found: {}".format(cam))
            # get most reasonable stream h x w < 350k
            res_limit = 350000
            stream_num = 0

            # use pafy to get the url of the stream
            # find stream with resolution within res_limit
            for i, stream in enumerate(videoPafy.streams):
                x, y = np.array(stream.resolution.split('x'), dtype=int)
                if x * y < res_limit:
                    stream_num = i
                else:
                    break
            stream = videoPafy.streams[stream_num]

            # test stream
            read_pass = self.__class__.__test_cam(stream.url)

            if read_pass:
                cam = stream.url
                print("YouTube Video Stream Detected!")
                print("Video Resolution : {}".format(stream.resolution))

        print("CAM SETUP:")
        print("Video Source     : {}".format(cam))
        print("Video Test       : {}".format("OK" if read_pass else "FAIL - check that streamer is publishing"))

        if not read_pass:
            raise Exception("Can't acquire video source: {}".format(cam))
        return cam

    def run(self):
        """
        Thread stops when capture is closed.
        """
        # get detector
        detector = DetectorFactory.get()

        # simplified access to elapsed time
        self.start_time = time.perf_counter()
        elapsed_time = lambda: time.perf_counter() - self.start_time

        # initialize loop variables
        last_detection_time = elapsed_time()
        frame_count = d_ctr = 0
        d_times = np.zeros(10)

        # open cam and start capture
        cap = cv2.VideoCapture(self.cam)
        print("CAM STARTED:")
        print("\tDetection        : {}".format("ON" if self.detection_on else "OFF"))
        print("\tDisplay FPS      : {}".format(self.display_fps))
        print("\tCamera FPS       : {}".format(self.cam_fps))
        print("\tDetections/min   : {}".format(self.dpm))

        # main loop
        self.running = True
        while cap.isOpened() and self.running:

            # loop until display fps reached
            c = 0
            while c < self.cam_fps / self.display_fps:
                c += int(cap.grab())

            # get next frame
            success = False
            cur_frame = None
            while not success:
                success, cur_frame = cap.read()
            frame_count += 1
            last_pull_time = elapsed_time()

            # if inference is on, perform detections each second
            try:
                if self.detection_on:
                    if last_pull_time - last_detection_time >= 60 / self.dpm:

                        last_detection_time = last_pull_time
                        d_ctr += 1

                        # put detected queue in ref queue
                        self.ref_queue.put((frame_count, self.det_queue))

                        # run detection on frame
                        frame_num, det_frame, detections = detector.detect(frame_num=frame_count,
                                                                           frame=cur_frame.copy())

                        det_frame = det_frame.copy()
                        # put in queue
                        self.det_queue.put((frame_num, det_frame))
                        self.detections_queue.put(detections)

                        # monitor detections
                        self.mon_queue.put((time.asctime(), detections, det_frame))

                    else:
                        # put undetected frame in queue
                        self.ref_queue.put((frame_count, self.undet_queue))
                        self.undet_queue.put((frame_count, cur_frame.copy()))

                else:  # detection is 'off'
                    # put undetected frame in reference queue
                    self.ref_queue.put((frame_count, self.undet_queue))
                    self.undet_queue.put((frame_count, cur_frame.copy()))

            except Exception as e:
                print("{} // run(): {}".format(self.getName(), e))

        cap.release()
        print("Exited '{}'!".format(self.getName()))

    def stop(self):
        self.running = False

    def is_running(self):
        return self.running

    def set_dpm(self, dpm: int):
        self.dpm = dpm

    def get_dpm(self):
        return self.dpm


