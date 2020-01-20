import cv2
import numpy as np

from modules.detectors.detector_factory import DetectorFactory
from modules.threads.thread import Thread
from modules.timers.elapsed_time import ElapsedTime
from modules.services.queue_service import add_frame, Frame


def add_overlay(frame: np.array, stats: dict) -> np.array:
    """
    Adds overly to current 'frame'.  Uses local variables
    stats and frame.  'stats' is a dictionary
    where keys are displayed statistics and values are the
    respective values.
    """
    # HELP MENU
    cv2.putText(frame, "{}".format("'q' - quit"),
                (10, frame.shape[0] - 10),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.4,
                color=(200, 0, 0),
                thickness=1)

    # STATISTICS
    # cv2.putText(frame, "{}".format("dpm: {}".format(round(capture_thread.get_dpm(), 1))),
    for i, (k, v) in enumerate(stats.items()):
        cv2.putText(frame, "{:14} : {}".format(k, round(v, 3)),
                    (frame.shape[1] - 180, frame.shape[0] - 10 - (i * 15)),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.4,
                    color=(200, 0, 0),
                    thickness=1)

    return frame


class VideoCaptureThread(Thread):
    """
    Thread that will read images from video stream.
    Places frames in queues depending on whether or not
    object detection was performed on the frame or not.
    Arguments are references to the queues where frames
    are put into.
    """
    def __init__(self, name: str, tm):
        Thread.__init__(self, name, thread_mgr=tm)
        self._elapsed_time = None

    def run(self):
        """
        Thread stops when capture is closed.
        """
        # get detector
        detector = None
        if self.tm.ps.DETECTION:
            detector = DetectorFactory.get(self.tm.ps.DETECTOR_NAME, self.tm.ps.DETECTOR_MODEL)
        print("Loaded detector!")

        # initialize loop variables
        frame_num = 0

        # open cam and start capture
        print("Starting cam ... ", end='\r')
        cap = cv2.VideoCapture(self.tm.ps.CAM_STREAM)

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
            while c < self.tm.ps.CAM_FPS / self.tm.ps.DISPLAY_FPS:
                c += int(cap.grab())

            # get next cam frame
            cur_frame = None
            while cur_frame is None:
                _, cur_frame = cap.read()
            last_pull_time = self._elapsed_time.get()
            frame_num += 1

            stats = {'dpm': round(self.tm.ps.DPM, 1),
                     'delay': round(self.tm.ps.BASE_DELAY, 3),
                     'buffer_size': self.tm.ref_queue.qsize(),
                     'elapsed_time': self._elapsed_time}

            q = self.tm.undet_queue
            detections = None
            frame = cur_frame.copy()

            # if detection/inference is on, perform detections at detection rate
            if self.tm.ps.DETECTION and last_pull_time - last_detection_time >= 60 / self.tm.ps.DPM:

                last_detection_time = last_pull_time

                try:
                    # run detection on frame
                    frame, detections = detector.detect(frame=cur_frame.copy())
                    q = self.tm.det_queue

                except Exception as e:
                    print("{} // run() DETECTION: {}".format(self.getName(), e))

            print("ADD OVERLAY         ", end='\r')
            frame = add_overlay(frame, stats)

            frame_tup = Frame(frame_num, last_pull_time, frame, q)

            add_frame(frame=frame_tup,
                      ref_queue=self.tm.ref_queue,
                      detections=detections,
                      detections_queue=self.tm.detections_queue,
                      mon_queue=self.tm.mon_queue)

        # release camera upon exit
        cap.release()

