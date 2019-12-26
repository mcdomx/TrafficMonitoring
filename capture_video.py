# ref: https://imageai.readthedocs.io/en/latest/detection/index.html

# This module will open a python video window with boxed recognized objects

import warnings
warnings.filterwarnings('ignore')

import cv2
import time, datetime
from imageai.Detection import VideoObjectDetection
from imageai.Detection import ObjectDetection
import os
import numpy as np
import json
import pafy
import queue
import threading
from abc import ABC


# SUPPORT FUNCTIONS
def get_dpm() -> int:
    return int(os.getenv("DPM", 20))


def get_display_fps() -> int:
    return int(os.getenv("DISPLAY_FPS", 30))


def convert_detections_to_counts(detections: list) -> dict:
    """
    Converts a single frame of detections into a
    dictionary of counts.
    """
    counts = {}
    for item in detections:
        obj_name = counts.get(item["name"])
        if obj_name == None:
            counts[item['name']] = 1
        else:
            counts[item['name']] += 1

    return counts


def convert_detections_to_avg_counts(minute_detections: list) -> dict:
    """
    Converts a minute of detections into a dictionary
    of items and their average counts.
    """
    frame_counts = []
    # first convert each frame detection into counts
    for frame_detections in minute_detections:
        frame_counts.append(convert_detections_to_counts(frame_detections))

    # then calculate the average
    counts = calc_avg_counts(frame_counts)

    return counts


def calc_avg_counts(frame_counts: list) -> dict:
    """
    Converts a list of frame counts into an average.
    """
    counts = {}
    # sum detections
    for frame_detections in frame_counts:
        for item, count in frame_detections.items():
            obj_name = counts.get(item)
            if obj_name == None:
                counts[item] = count
            else:
                counts[item] += count

    # convert counts to averages
    for k, v in counts.items():
        counts[k] = v / len(frame_counts)

    return counts


def setup_cam():
    """
    Test video stream and returns the camera, log boolean and model_name
    """
    cam = os.getenv("CAM_STREAM", 0)
    if cam.isdigit():
        cam = int(cam)

    # test video feed
    cap = cv2.VideoCapture(cam)
    read_pass = cap.grab()
    cap.release()

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
        for i, stream in enumerate(videoPafy.streams):
            x, y = np.array(stream.resolution.split('x'), dtype=int)
            if x * y < res_limit:
                stream_num = i
            else:
                break
        stream = videoPafy.streams[stream_num]

        cap = cv2.VideoCapture(stream.url)
        read_pass = cap.grab()
        cap.release()
        if read_pass:
            cam = stream.url
            print("YouTube Video Stream Detected!")
            print("Video Resolution : {}".format(stream.resolution))
        else:  # no video found
            raise Exception("YouTube video failed: {}".format(cam))

    print("Video Source     : {}".format(cam))
    print("Video Test       : {}".format("OK" if read_pass else "FAIL - check that streamer is publishing"))

    return cam

# END SUPPORT FUNCTIONS


# DETECTOR SUPPORT
class Detector(ABC):
    """
    Abstract class for a detector.
    required methods:
    > detect(frame_num:int, frame:np.array) -> int, np.array
        - returns the frame number and frame with detections
    """

    def detect(self, frame_num: int, frame: np.array) -> (int, np.array, list):
        ...



def get_object_detector() -> Detector:
    """
    Returns Detecor object.
    Update this function to add new detection models.
    New moidels will require new class that inherits from Detector class.
    """

    det = os.getenv("DETECTOR", "imageai")

    if det == 'imageai':
        return Object_Detector_imageai()


class Object_Detector_imageai(Detector):
    """
    Sets the object detection with the ImageAI implementation.
    http://imageai.org.

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


# END DETECTOR SUPPORT

# LOGGING THREAD
class log_detections_thread(threading.Thread):
    """
    Log detections to file.
    At each interval (usu. 1 second) detections are added to a list.
    This thread will convert that list into the averages for the
    logging period (usu. 1 minute).
    """

    def __init__(self, detections_queue, read_thread):
        threading.Thread.__init__(self)
        self.detections_queue = detections_queue
        self.read_thread = read_thread
        self.running = False

    def run(self):
        """
        go through detections list
        add detected items to dictionary
        """
        start_time = time.perf_counter()
        elapsed_time = lambda: time.perf_counter() - start_time
        minute_counter = elapsed_time()

        self.running = True

        while self.running:

            while elapsed_time() - minute_counter < 60 and self.running:
                time.sleep(1)
            minute_counter = elapsed_time()

            cap_time = datetime.datetime.now()

            # get detections from queue
            det_list = []
            while not self.detections_queue.empty():
                det_list.append(self.detections_queue.get())

            # auto-throttle detection rate
            cur_dpm = self.read_thread.get_dpm()
            act_dpm = len(det_list)
            if cur_dpm > act_dpm:  # throttle down
                self.read_thread.set_dpm(act_dpm + int((cur_dpm - act_dpm) / 2))
            else:  # throttle up
                self.read_thread.set_dpm(act_dpm + 1)

            # convert detections to avg counts
            minute_counts = convert_detections_to_avg_counts(det_list)

            # Log data to file
            if len(minute_counts) > 0:
                log_filepath = os.getenv("LOG_FILEPATH", "./logdir/camlogs.txt")
                self.log_counts(cap_time, log_filepath, minute_counts)

            print("\n\t{}   # detections: {}".format(cap_time, len(det_list)))
            print("\tAvg/Min: ", end='')
            for k, v in minute_counts.items():
                print("{}:{}".format(k, round(v, 2)), end='  ')
            print("")

        print("Exited '{}'!".format(self.getName()))

    def log_counts(self, cap_time, log_filepath, counts):

        save_time = datetime.datetime(year=cap_time.year,
                                      month=cap_time.month,
                                      day=cap_time.day,
                                      hour=cap_time.hour,
                                      minute=cap_time.minute)

        # insert header for first record
        if not os.path.isfile(log_filepath):
            with open(log_filepath, 'w') as fp:
                fp.write("date_time|day_minute|object|count\n")

        with open(log_filepath, 'a') as fp:
            for k, v in counts.items():
                fp.write(str(save_time))
                fp.write('|')
                fp.write("{}".format(cap_time.hour * 60 + cap_time.minute))  # day_minute
                fp.write('|')
                fp.write(k)
                fp.write('|')
                fp.write("{}".format(round(v, 6)))
                fp.write('\n')

    def stop(self):
        self.running = False
# END LOGGING THREAD


# READ THREAD

class read_stream_thread(threading.Thread):
    """
    Thread that will read images from video stream.
    Places frames in queues depending on whether or not
    object detection was performed on the frame or not.
    Arguments are references to the queues where frames
    are put into.
    """

    def __init__(self,
                 ref_queue: queue.Queue,
                 det_queue: queue.Queue,
                 undet_queue: queue.Queue,
                 detections_queue: queue.Queue):
        threading.Thread.__init__(self)
        self.ref_queue = ref_queue
        self.det_queue = det_queue
        self.undet_queue = undet_queue
        self.detections_queue = detections_queue
        self.running = False
        self.dpm = get_dpm()  # detections per minute
        self.display_fps = get_display_fps()  # local display fps
        self.start_time = None
        self.detection_on = True if os.getenv("DETECTION", 'True') == "True" else False
        self.cam = setup_cam()
        self.cap = cv2.VideoCapture(self.cam)
        self.cam_fps = self.cap.get(cv2.CAP_PROP_FPS)

        # If camera rate is lower that the display rate,
        # set the display_rate equal to camera_rate
        if self.display_fps > self.cam_fps:
            self.display_fps = self.cam_fps

        print("CAM SETUP:")
        print("\tDetection        : {}".format("ON" if self.detection_on else "OFF"))
        print("\tDisplay FPS      : {}".format(self.display_fps))
        print("\tCamera FPS       : {}".format(self.cam_fps))
        print("\tDetections/min   : {}".format(self.dpm))

    def run(self):
        """
        Thread stops when capture is closed.
        """
        print("Started video capture!")

        od = get_object_detector()

        # simplied access to elapsed time
        self.start_time = time.perf_counter()
        elapsed_time = lambda: time.perf_counter() - self.start_time

        # initialize loop variables
        last_pull_time = last_detection_time = elapsed_time()
        displayed_frames = last_detection_frame = interval_counter = 0

        self.running = True
        while self.cap.isOpened() and self.running:

            # loop until display fps reached
            while interval_counter < self.cam_fps / self.display_fps:
                interval_counter += int(self.cap.grab())
            interval_counter = 0

            # get next frame
            success = False
            while not success:
                success, cur_frame = self.cap.read()
            displayed_frames += 1
            last_pull_time = elapsed_time()

            # if inference is on, perform detections each second
            try:
                if self.detection_on:
                    if last_pull_time - last_detection_time >= 60 / self.dpm:

                        last_detection_time = last_pull_time

                        # put detected queue in ref queue
                        self.ref_queue.put((displayed_frames, self.det_queue))

                        # run detection on frame
                        frame_num, det_frame, detections = od.detect(displayed_frames, cur_frame.copy())

                        # put in queue
                        self.det_queue.put((frame_num, det_frame))
                        self.detections_queue.put(detections)

                    else:
                        # put undetected frame in queue
                        self.ref_queue.put((displayed_frames, self.undet_queue))
                        self.undet_queue.put((displayed_frames, cur_frame.copy()))

                else:  # detection is 'off'
                    # put undetected frame in reference queue
                    self.ref_queue.put((displayed_frames, self.undet_queue))
                    self.undet_queue.put((displayed_frames, cur_frame.copy()))

            except Exception as e:
                print("{} // run(): {}".format(self.getName(), e))

        self.cap.release()
        print("Exited '{}'!".format(self.getName()))

    def stop(self):
        self.running = False

    def is_running(self):
        return self.running

    def get_camfps(self):
        if not self.is_running:
            print("Cam not setup yet.")
            return False
        return self.cam_fps

    def set_dpm(self, dpm: int):
        self.dpm = dpm

    def get_dpm(self):
        return self.dpm


# END READ_THREAD


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

    The routine can be stopped by pressing 'q' while the video
    window is selected.

    """

    def terminate_threads():
        for t in thread_list:
            print("Closing '{}' ... ".format(t.getName()), end='\r')
            t.stop()  # signal thread to stop
            t.join()  # wait until it is stopped
            print("'{}' closed!     ".format(t.getName()))

    def add_overlay(frame: np.array) -> np.array:
        cv2.putText(frame, "{}".format("'q' - quit"),
                    (10, frame.shape[0] - 10),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.4,
                    color=(0, 200, 0),
                    thickness=1)
        cv2.putText(frame, "{}".format("dpm: {}".format(capture_thread.get_dpm())),
                    (frame.shape[1] - 60, frame.shape[0] - 10),
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
    buffer_size = 128
    ref_queue = queue.Queue(buffer_size)  # includes frame num and queue to get frame from
    det_queue = queue.Queue(buffer_size)  # includes frames with processed detections
    undet_queue = queue.Queue(buffer_size)  # includes frame without detections
    detections_queue = queue.Queue()  # includes detections for the logging interval period

    # start thread to read video
    capture_thread = read_stream_thread(ref_queue,
                                        det_queue,
                                        undet_queue,
                                        detections_queue)
    capture_thread.setName("capture-thread")
    #     capture_thread.daemon = True
    capture_thread.start()
    thread_list.append(capture_thread)

    # wait till the camera is setup in the reading thread
    while capture_thread.get_camfps() == 0:
        time.sleep(1)

    # get the source's fps rate
    cam_fps = capture_thread.get_camfps()

    # start logging thread
    if os.getenv("LOGGING", "True")=="True":
        logging_thread = log_detections_thread(detections_queue,
                                               capture_thread)
        logging_thread.setName("logging-thread")
        #         logging_thread.daemon = True
        logging_thread.start()
        thread_list.append(logging_thread)

    # simplified access to elapsed time
    start_time = time.perf_counter()
    elapsed_time = lambda: time.perf_counter() - start_time

    # initialize variables
    last_display_time = 0

    # main display loop - main thread
    while (True):

        if elapsed_time() - last_display_time < 1 / cam_fps:
            continue

        print("{:90}".format(" "), end='\r')  # clear line
        print("Elapsed time: {:<8} Buffer size: {:<3} ".format(round(elapsed_time(), 1), ref_queue.qsize()), end='\r')

        try:
            frame_num, source_queue = ref_queue.get()
            ref_queue.task_done()
            frame_num, frame = source_queue.get()
            source_queue.task_done()

            last_display_time = elapsed_time()

            # frame overlay
            add_overlay(frame)

            # update window
            cv2.imshow(window_name, frame)

            # wait briefly to interpret keystroke
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\nTerminating video feed! 'q' Pressed.")
                cv2.destroyWindow(window_name)
                cv2.waitKey(1)  # flushes command
                break

            # pause to smooth video stream
            delay = .025
            # pause extra to display captures
            if source_queue is det_queue:
                delay += .2
            # pause more as qsize gets smaller
            time.sleep(1 / (ref_queue.qsize() + 2) + delay)

        except Exception as e:  # in case of failure, continue
            print("Main thread: {}".format(e))
            continue

    # terminate threads
    terminate_threads()


if __name__ == "__main__":
    stream_object_detection()
