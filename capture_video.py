import warnings
import cv2
import time
import os
import numpy as np
import queue
from modules.Logging.LoggingThread import LoggingThread
from modules.Monitoring.Monitor import Monitor
from modules.Video_Capture.VideoCaptureThread import VideoCaptureThread

warnings.filterwarnings('ignore')


def get_dpm() -> int:
    return int(os.getenv("DPM", 20))


def get_display_fps() -> int:
    return int(os.getenv("DISPLAY_FPS", 30))


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

    def terminate_threads():
        for t in thread_list:
            print("Closing '{}' ... ".format(t.getName()), end='\r')
            t.stop()  # signal thread to stop
            t.join()  # wait until it is stopped
            print("'{}' closed!     ".format(t.getName()))

    # def add_overlay(frame: np.array, stats:dict = None) -> np.array:
    def add_overlay() -> np.array:
        # frame[frame.shape[0] - 10: frame.shape[0] - 30, 10:20] = np.int(frame[frame.shape[0] - 10: frame.shape[0] - 30, 10:20] / 2)
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

    # list of threads
    thread_list = []

    # 4 queues are used.
    # 'det_queue'   : Holds tuples for each frame with detected objects.
    #                 tuple(frame_num, frame_image)
    # 'undet_queue' : Holds tuples for each frame with no detected objects.
    #                 tuple(frame_num, frame_image)
    # 'ref_queue'   : Holds tuples for each frame captured.
    #                 tuple(frame_num, queue_of_frame_image)
    # 'detections_queue' : Holds lists of detected objects from each detected frame
    buffer_size = 256
    ref_queue = queue.Queue(buffer_size)  # includes frame num and queue to get frame from
    det_queue = queue.Queue(buffer_size)  # includes frames with processed detections
    undet_queue = queue.Queue(buffer_size)  # includes frame without detections
    detections_queue = queue.Queue()  # includes detections for the logging interval period
    mon_queue = queue.Queue()  # used to monitor detections (time, detections, image)

    # start thread to read video
    capture_thread = VideoCaptureThread(ref_queue,
                                        det_queue,
                                        undet_queue,
                                        detections_queue,
                                        mon_queue,
                                        dpm=get_dpm(),
                                        display_fps=get_display_fps())
    capture_thread.setName("capture-thread")
    capture_thread.start()
    thread_list.append(capture_thread)

    # get the source's fps rate
    cam_fps = 0
    while cam_fps == 0:
        cam_fps = capture_thread.get_camfps()
        time.sleep(.2)
        print("waiting for fps rate....", end='')
    print("FPS={}".format(cam_fps))

    # start logging thread
    if os.getenv("LOGGING", "True") == "True":
        logging_thread = LoggingThread(detections_queue,
                                       capture_thread)
        logging_thread.setName("logging-thread")
        logging_thread.start()
        thread_list.append(logging_thread)

    # start monitoring thread
    if os.getenv("MONITORING", "True") == "True":
        monitoring_thread = Monitor(mon_queue=mon_queue)
        monitoring_thread.setName("monitoring-thread")
        monitoring_thread.start()
        thread_list.append(monitoring_thread)

    # simplify access to elapsed time
    start_time = time.perf_counter()
    elapsed_time = lambda: time.perf_counter() - start_time

    # initialize variables
    last_display_time = 0
    delay = 0 #.03 Set to smooth video - adjusted with '[' and ']' keys.
    t_delay = 0

    # main display loop - main thread
    while True:

        if elapsed_time() - last_display_time < 1 / cam_fps:
            continue

        print("{:90}".format(" "), end='\r')  # clear line
        print("Elapsed time: {:<8} Buffer size: {:<3} delay: {}".format(round(elapsed_time(), 1), ref_queue.qsize(), delay), end='\r')

        try:
            frame_num, source_queue = ref_queue.get()
            ref_queue.task_done()
            frame_num, frame = source_queue.get()
            source_queue.task_done()

            last_display_time = elapsed_time()

            # frame overlay
            stats = {}
            stats['dpm'] = round(capture_thread.get_dpm(), 1)
            stats['delay'] = t_delay
            add_overlay()

            # update window
            cv2.imshow(window_name, frame)

            # wait briefly to interpret keystroke
            keypress = cv2.waitKeyEx(1)
            if keypress == 113: #cv2.waitKeyEx(1) & 0xFF == ord('q'):
                print("\nTerminating video feed! 'q' Pressed.")
                cv2.destroyWindow(window_name)
                cv2.waitKey(1)  # flushes command
                break
            elif keypress == 32:  # space bar
                cv2.imwrite("./logdir/{}.png".format(elapsed_time()), frame)
                # time.sleep(.05)
            elif keypress == 93:  # left bracket
                delay += .005
            elif keypress == 91:  # right bracket
                delay = max((0, delay - .005))

            # pause to smooth video stream
            # delay = .03
            # pause extra to display captures
            frame_delay = 0
            if source_queue is det_queue:
                frame_delay += .25
            # pause more as buffer gets smaller
            t_delay = 1 / (ref_queue.qsize() + 2) + delay + frame_delay
            time.sleep(t_delay)

        except Exception as e:  # in case of failure, continue
            print("Main thread: {}".format(e))
            continue

    # terminate threads
    terminate_threads()


if __name__ == "__main__":
    stream_object_detection()
