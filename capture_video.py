# import warnings
# import time
# # import threading
#
# import cv2
# import numpy as np
#
# from modules.threads.logging_thread import LoggingThread
# from modules.threads.monitoring_thread import MonitorThread
# from modules.threads.video_capture_thread import VideoCaptureThread
# from modules.services.queue_service import QueueService
# from modules.services.parameters import Params
# from modules.threads.thread import Thread
# from modules.timers.elapsed_time import ElapsedTime
#
#
# warnings.filterwarnings('ignore')
#
#
# # def add_overlay(frame: np.array, stats:dict = None) -> np.array:
# def add_overlay(frame: np.array, stats: dict) -> np.array:
#     """
#     Adds overly to current 'frame'.  Uses local variables
#     stats and frame.  'stats' is a dictionary
#     where keys are displayed statistics and values are the
#     respective values.
#     """
#     # HELP MENU
#     cv2.putText(frame, "{}".format("'q' - quit"),
#                 (10, frame.shape[0] - 10),
#                 fontFace=cv2.FONT_HERSHEY_SIMPLEX,
#                 fontScale=0.4,
#                 color=(0, 200, 0),
#                 thickness=1)
#
#     # STATISTICS
#     # cv2.putText(frame, "{}".format("dpm: {}".format(round(capture_thread.get_dpm(), 1))),
#     for i, (k, v) in enumerate(stats.items()):
#         cv2.putText(frame, "{:6} : {}".format(k, round(v, 3)),
#                     (frame.shape[1] - 100, frame.shape[0] - 10 - (i * 15)),
#                     fontFace=cv2.FONT_HERSHEY_SIMPLEX,
#                     fontScale=0.4,
#                     color=(0, 200, 0),
#                     thickness=1)
#
#     return frame
#
#
# def get_frame(stats: dict = None, qs=QueueService()) -> (int, np.array, float):
#     frame_num, source_queue = qs.ref_queue.get()
#     qs.ref_queue.task_done()
#     frame_num, frame = source_queue.get()
#     source_queue.task_done()
#
#     # frame overlay
#     if stats:
#         frame = add_overlay(frame, stats)
#
#     # pause extra to display captures
#     f_delay = 0
#     if source_queue is qs.det_queue:
#         f_delay = .25
#
#     return frame_num, frame, f_delay
#
#
# def update_window(d_delay: float, elapsed_time: ElapsedTime, p=Params()):
#     """
#     Update cv window with images from queue.
#     :return: -1 if 'q' pressed, else returns floats of
#                 display delay and frame delay
#     """
#     # set display window title bar text
#     window_name = "Traffic Monitor"
#     f_delay = 0
#
#     try:
#         # frame_num, source_queue = qs.ref_queue.get()
#         # qs.ref_queue.task_done()
#         # frame_num, frame = source_queue.get()
#         # source_queue.task_done()
#
#         stats = {}
#         stats.setdefault('dpm', round(p.DPM, 1))
#         stats.setdefault('delay', d_delay)
#         frame_num, frame, f_delay = get_frame(stats)
#
#         # update window
#         cv2.imshow(window_name, frame)
#
#         # wait briefly to interpret keystroke
#         keypress = cv2.waitKeyEx(1)
#         if keypress == 113:  # cv2.waitKeyEx(1) & 0xFF == ord('q'):
#             print("\nTerminating video feed! 'q' Pressed.")
#             cv2.destroyWindow(window_name)
#             cv2.waitKey(1)  # flushes command
#             return -1, -1
#         elif keypress == 32:  # space bar
#             cv2.imwrite("./logs/images/{}.png".format(elapsed_time.get()), frame)
#         elif keypress == 93:  # left bracket
#             d_delay = round(d_delay + .005, 3)
#         elif keypress == 91:  # right bracket
#             d_delay = max((0, round(d_delay - .005, 3)))
#
#     except Exception as e:  # in case of failure, continue
#         print("Main thread: {}".format(e))
#
#     return d_delay, f_delay
#
#
# def stream_object_detection(p=Params(), qs=QueueService()):
#     """
#     This routine will stream a video and perform object detection
#     on frames captured from the video.
#     Object detection is auto-throttled by the corresponding
#     read_thread.
#
#     This routine uses threading to improve performance.  The main
#     thread will display images.  The read_thread will capture
#     images from the source and perform inference.  The rate of
#     inference is auto-throttled.
#
#     If logging is enabled, the read_thread will launch a sub-thread
#     that will log the detection statistics to file once per minute.
#
#     If monitoring is enabled (true by default), a monitoring thread
#     is launched.
#
#     The routine can be stopped by pressing 'q' while the video
#     window is selected.
#
#     """
#
#     # start threads
#     VideoCaptureThread("capture-thread")
#     LoggingThread("logging-thread")
#     MonitorThread("monitoring-thread")
#
#     # initialize variables
#     last_display_time = 0
#     delay = 0.05  # Set to smooth video - adjusted with '[' and ']' keys.
#
#     # start timer
#     elapsed_time = ElapsedTime()
#
#     # main display loop - main thread
#     while True:
#
#         if elapsed_time.get() - last_display_time < 1 / p.CAM_FPS:
#             continue
#
#         print("{:90}".format(" "), end='\r')  # clear line
#         print("Elapsed time: {:<8} Buffer size: {:<3} delay: {}".format(round(elapsed_time.get(), 1),
#                                                                         qs.ref_queue.qsize(),
#                                                                         delay), end='\r')
#
#         last_display_time = elapsed_time.get()
#
#         if p.SHOW_VIDEO:
#             # update display window
#             delay, frame_delay = update_window(delay, elapsed_time)
#
#             # stop loop if 'q' pressed
#             if delay < 0:
#                 break
#
#             # pause for a moment
#             time.sleep(1 / (qs.ref_queue.qsize() + 2) + delay + frame_delay)
#
#     # terminate all threads
#     Thread.terminate_threads()
#
#
# if __name__ == "__main__":
#     stream_object_detection()
