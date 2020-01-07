# import threading
import time

import cv2

from modules.detectors.detector_factory import DetectorFactory
from modules.threads.thread import Thread
from modules.timers.elapsed_time import ElapsedTime
# from modules.services.parameters import Params
#
# p = Params()


class VideoCaptureThread(Thread):
    """
    Thread that will read images from video stream.
    Places frames in queues depending on whether or not
    object detection was performed on the frame or not.
    Arguments are references to the queues where frames
    are put into.
    """
    def __init__(self, name):
        Thread.__init__(self, name)
        self._elapsed_time = None

    def run(self):
        """
        Thread stops when capture is closed.
        """
        # get detector
        detector = None
        if self._p.DETECTION:
            detector = DetectorFactory.get(self._p.DETECTOR_NAME, self._p.DETECTOR_MODEL)

        # initialize loop variables
        frame_count = 0

        # open cam and start capture
        cap = cv2.VideoCapture(self._p.CAM_STREAM)

        # main loop
        self._running = True
        if self._running and cap.isOpened():
            print("CAM STARTED!")

        # start timer
        self._elapsed_time = ElapsedTime()
        last_detection_time = 0

        while cap.isOpened() and self._running:

            # loop until display fps reached
            c = 0
            while c < self._p.CAM_FPS / self._p.DISPLAY_FPS:
                c += int(cap.grab())

            # get next frame
            # success = False
            cur_frame = None
            while cur_frame is None:
                _, cur_frame = cap.read()
            frame_count += 1
            last_pull_time = self._elapsed_time.get()

            # if inference is on, perform detections each second
            try:
                if self._p.DETECTION:
                    if last_pull_time - last_detection_time >= 60 / self._p.DPM:

                        last_detection_time = last_pull_time

                        # put detected queue in ref queue
                        self._qs.ref_queue.put((frame_count, self._qs.det_queue))

                        # run detection on frame
                        frame_num, det_frame, detections = detector.detect(frame_num=frame_count,
                                                                           frame=cur_frame.copy())

                        det_frame = det_frame.copy()
                        # put in queue
                        self._qs.det_queue.put((frame_num, det_frame))
                        self._qs.detections_queue.put(detections)

                        # monitor detections
                        # need to queue dict in order for get to function with time
                        self._qs.mon_queue.put({"t": time.time(), "d": detections, "f": det_frame})

                    else:
                        # put undetected frame in queue
                        self._qs.ref_queue.put((frame_count, self._qs.undet_queue))
                        self._qs.undet_queue.put((frame_count, cur_frame.copy()))

                else:  # detection is 'off'
                    # put undetected frame in reference queue
                    self._qs.ref_queue.put((frame_count, self._qs.undet_queue))
                    self._qs.undet_queue.put((frame_count, cur_frame.copy()))

            except Exception as e:
                print("{} // run(): {}".format(self.getName(), e))

        # release camera upon exit
        cap.release()

