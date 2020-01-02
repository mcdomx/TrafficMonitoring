import threading
import time

import cv2

from modules.detectors.detector_factory import DetectorFactory
from modules.queue_service import QueueService
from modules.parameters import Params

p = Params()


class VideoCaptureThread(threading.Thread):
    """
    Thread that will read images from video stream.
    Places frames in queues depending on whether or not
    object detection was performed on the frame or not.
    Arguments are references to the queues where frames
    are put into.
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.qs = QueueService()
        self.running = False
        self.start_time = None

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

        # open cam and start capture
        cap = cv2.VideoCapture(p.CAM_STREAM)

        # main loop
        self.running = True
        if self.running and cap.isOpened():
            print("CAM STARTED!")
        while cap.isOpened() and self.running:

            # loop until display fps reached
            c = 0
            while c < p.CAM_FPS / p.DISPLAY_FPS:
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
                if p.DETECTION:
                    if last_pull_time - last_detection_time >= 60 / p.DPM:

                        last_detection_time = last_pull_time
                        d_ctr += 1

                        # put detected queue in ref queue
                        self.qs.ref_queue.put((frame_count, self.qs.det_queue))

                        # run detection on frame
                        frame_num, det_frame, detections = detector.detect(frame_num=frame_count,
                                                                           frame=cur_frame.copy())

                        det_frame = det_frame.copy()
                        # put in queue
                        self.qs.det_queue.put((frame_num, det_frame))
                        self.qs.detections_queue.put(detections)

                        # monitor detections
                        self.qs.mon_queue.put((time.asctime(), detections, det_frame))

                    else:
                        # put undetected frame in queue
                        self.qs.ref_queue.put((frame_count, self.qs.undet_queue))
                        self.qs.undet_queue.put((frame_count, cur_frame.copy()))

                else:  # detection is 'off'
                    # put undetected frame in reference queue
                    self.qs.ref_queue.put((frame_count, self.qs.undet_queue))
                    self.qs.undet_queue.put((frame_count, cur_frame.copy()))

            except Exception as e:
                print("{} // run(): {}".format(self.getName(), e))

        cap.release()
        print("Exited '{}'!".format(self.getName()))

    def stop(self):
        self.running = False

    def is_running(self):
        return self.running



