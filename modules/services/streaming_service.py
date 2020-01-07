import warnings
import time

import cv2
import numpy as np

from modules.threads.thread import Thread
from modules.timers.elapsed_time import ElapsedTime


warnings.filterwarnings('ignore')


class StreamingService(Thread):
    """
    Main video streaming service.
    This will launch necessary threads to capture and present
    a video stream with object detection.
    """
    def __init__(self, name):
        Thread.__init__(self, name)
        self._elapsed_time = None

    # def add_overlay(frame: np.array, stats:dict = None) -> np.array:
    @staticmethod
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
                    color=(0, 200, 0),
                    thickness=1)

        # STATISTICS
        # cv2.putText(frame, "{}".format("dpm: {}".format(round(capture_thread.get_dpm(), 1))),
        for i, (k, v) in enumerate(stats.items()):
            cv2.putText(frame, "{:6} : {}".format(k, round(v, 3)),
                        (frame.shape[1] - 100, frame.shape[0] - 10 - (i * 15)),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.4,
                        color=(0, 200, 0),
                        thickness=1)

        return frame

    def get_frame(self, stats: dict = None) -> (int, np.array, float):
        frame_num, source_queue = self._qs.ref_queue.get()
        self._qs.ref_queue.task_done()
        frame_num, frame = source_queue.get()
        source_queue.task_done()

        # frame overlay
        if stats:
            frame = self.__class__.add_overlay(frame, stats)

        # pause extra to display captures
        f_delay = 0
        if source_queue is self._qs.det_queue:
            f_delay = .25

        return frame_num, frame, f_delay

    def update_window(self, d_delay: float):
        """
        Update cv window with images from queue.
        :return: -1 if 'q' pressed, else returns floats of
                    display delay and frame delay
        """
        # set display window title bar text
        window_name = "Traffic Monitor"
        f_delay = 0

        try:
            # frame_num, source_queue = qs.ref_queue.get()
            # qs.ref_queue.task_done()
            # frame_num, frame = source_queue.get()
            # source_queue.task_done()

            stats = {}
            stats.setdefault('dpm', round(self._p.DPM, 1))
            stats.setdefault('delay', d_delay)
            frame_num, frame, f_delay = self.get_frame(stats)

            # update window
            cv2.imshow(window_name, frame)

            # wait briefly to interpret keystroke
            keypress = cv2.waitKeyEx(1)
            if keypress == 113:  # cv2.waitKeyEx(1) & 0xFF == ord('q'):
                print("\nTerminating video feed! 'q' Pressed.")
                cv2.destroyWindow(window_name)
                cv2.waitKey(1)  # flushes command
                return -1, -1
            elif keypress == 32:  # space bar
                cv2.imwrite("./logs/images/{}.png".format(self._elapsed_time.get()), frame)
            elif keypress == 93:  # left bracket
                d_delay = round(d_delay + .005, 3)
            elif keypress == 91:  # right bracket
                d_delay = max((0, round(d_delay - .005, 3)))

        except Exception as e:  # in case of failure, continue
            print("Main thread: {}".format(e))

        return d_delay, f_delay

    def run(self):
        """
        This routine will stream a video and perform object detection
        on frames captured from the video.
        Object detection is auto-throttled by the corresponding
        read_thread.

        This routine uses threading to improve performance.  The main
        thread will display images.  The read_thread will capture
        images from the source and perform inference.  The rate of
        inference is auto-throttled.

        If logging is enabled, the read_thread will launch a sub-thread
        that will log the detection statistics to file once per minute.

        If monitoring is enabled (true by default), a monitoring thread
        is launched.

        The routine can be stopped by pressing 'q' while the video
        window is selected.

        """

        # start threads
        # VideoCaptureThread("capture-thread")
        # LoggingThread("logging-thread")
        # MonitorThread("monitoring-thread")

        # initialize variables
        last_display_time = 0
        delay = 0.05  # Set to smooth video - adjusted with '[' and ']' keys.

        # start timer
        self._elapsed_time = ElapsedTime()

        # main display loop - main thread
        while True:

            if self._elapsed_time.get() - last_display_time < 1 / self._p.CAM_FPS:
                continue

            print("{:90}".format(" "), end='\r')  # clear line
            print("Elapsed time: {:<8} Buffer size: {:<3} delay: {}".format(round(self._elapsed_time.get(), 1),
                                                                            self._qs.ref_queue.qsize(),
                                                                            delay), end='\r')

            last_display_time = self._elapsed_time.get()

            if self._p.SHOW_VIDEO:
                # update display window
                delay, frame_delay = self.update_window(delay)

                # stop loop if 'q' pressed
                if delay < 0:
                    break

                # pause for smoothing - extra pause to show detections
                time.sleep(1 / (self._qs.ref_queue.qsize() + 2) + delay + frame_delay)

        # terminate all threads if loop exits
        Thread.terminate_threads()
