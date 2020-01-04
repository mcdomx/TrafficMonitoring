import warnings
import time
import threading

import cv2
import numpy as np

from modules.logging.logging_thread import LoggingThread
from modules.monitoring.monitoring_thread import Monitor
from modules.Video_Capture.video_capture_thread import VideoCaptureThread
from modules.queue_service import QueueService
from modules.parameters import Params


warnings.filterwarnings('ignore')


def stream_object_detection():
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
    def start_thread(t: threading.Thread, name: str):
        t.setName(name)
        t.start()
        return t

    def terminate_threads():
        for t in thread_list:
            print("Closing '{}' ... ".format(t.getName()), end='\r')
            t.stop()  # signal thread to stop
            t.join()  # wait until it is stopped
            print("'{}' closed!     ".format(t.getName()))

    # def add_overlay(frame: np.array, stats:dict = None) -> np.array:
    def add_overlay() -> np.array:
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
                        (frame.shape[1] - 100, frame.shape[0] - 10 - (i*15)),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.4,
                        color=(0, 200, 0),
                        thickness=1)

    # set display window title bar text
    window_name = "Traffic Monitor"

    # initialize parameters
    p = Params()

    # initialize queue service
    qs = QueueService()

    # start threads
    thread_list = [
                    start_thread(VideoCaptureThread(), "capture-thread"),
                    start_thread(LoggingThread(), "logging-thread"),
                    start_thread(Monitor(), "monitoring-thread")
                    ]

    # simplify access to elapsed time
    start_time = time.perf_counter()
    elapsed_time = lambda: time.perf_counter() - start_time

    # initialize variables
    last_display_time = 0
    delay = 0.045  # .03 Set to smooth video - adjusted with '[' and ']' keys.
    t_delay = 0

    # main display loop - main thread
    while True:

        if elapsed_time() - last_display_time < 1 / p.CAM_FPS:
            continue

        print("{:90}".format(" "), end='\r')  # clear line
        print("Elapsed time: {:<8} Buffer size: {:<3} delay: {}".format(round(elapsed_time(), 1), qs.ref_queue.qsize(), delay), end='\r')

        try:
            frame_num, source_queue = qs.ref_queue.get()
            qs.ref_queue.task_done()
            frame_num, frame = source_queue.get()
            source_queue.task_done()

            last_display_time = elapsed_time()

            if p.SHOW_VIDEO:
                # frame overlay
                stats = {}
                stats.setdefault('dpm', round(p.DPM, 1))
                stats.setdefault('delay', t_delay)
                add_overlay()

                # update window
                cv2.imshow(window_name, frame)

                # wait briefly to interpret keystroke
                keypress = cv2.waitKeyEx(1)
                if keypress == 113:  # cv2.waitKeyEx(1) & 0xFF == ord('q'):
                    print("\nTerminating video feed! 'q' Pressed.")
                    cv2.destroyWindow(window_name)
                    cv2.waitKey(1)  # flushes command
                    break
                elif keypress == 32:  # space bar
                    cv2.imwrite("./logdir/{}.png".format(elapsed_time()), frame)
                elif keypress == 93:  # left bracket
                    delay = round(delay + .005, 3)
                elif keypress == 91:  # right bracket
                    delay = max((0, round(delay - .005, 3)))

                # pause extra to display captures
                frame_delay = 0
                if source_queue is qs.det_queue:
                    frame_delay += .25
                # pause more as buffer gets smaller
                t_delay = 1 / (qs.ref_queue.qsize() + 2) + delay + frame_delay
                time.sleep(t_delay)

        except Exception as e:  # in case of failure, continue
            print("Main thread: {}".format(e))
            continue

    # terminate threads
    terminate_threads()


if __name__ == "__main__":
    stream_object_detection()
