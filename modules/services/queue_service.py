import queue
import numpy as np
import time


class QueueService(object):
    """
    Singleton class.
    Holds queues necessary for video capture, inference and display.

    # 5 queues are used.
            # 'det_queue'        : Holds tuples for each frame with detected objects.
            #                      tuple(elapsed_time, frame_image)
            # 'undet_queue'      : Holds tuples for each frame with no detected objects.
            #                      tuple(elapsed_time, frame_image)
            # 'ref_queue'        : Holds tuples for each frame captured.
            #                      tuple(elapsed_time, queue_of_frame_image)
            # 'detections_queue' : Holds lists of detected objects from each detected frame
            # 'mon_queue'        : Holds items in each detection that will be checked for monitoring
                                   {'t':time 'd':detections 'f':frame}
    """
    # _s = None  # singleton instance
    #
    # def __new__(cls, buffer_size: int = 256):
    #     if cls._s is None:
    #         cls._s = super(QueueService, cls).__new__(cls)
    #     elif buffer_size != cls._s.get_buffersize():
    #         print("Buffer size cannot be changed: {}".format(cls._s.buffer_size))
    #     return cls._s

    # class __Singleton:
    def __init__(self, buffer_size: int = 128):
        self.buffer_size = buffer_size
        self.ref_queue = queue.Queue(buffer_size)  # includes frame num and queue to get frame from
        self.det_queue = queue.Queue(buffer_size)  # includes frames with processed detections
        self.undet_queue = queue.Queue(buffer_size)  # includes frame without detections
        self.detections_queue = queue.Queue(buffer_size)  # includes detections for the logging interval period
        self.mon_queue = queue.Queue(20)  # used to monitor detections (time, detections:set, image:np.array)

        print("Queue Service Established")

    def get_buffersize(self) -> int:
        return self.buffer_size

    # GET AND ADD FRAMES FROM/TO QUEUES ##################################
    def get_frame(self) -> (int, np.array):
        """
        Get the next frame in the queue.
        :return: frame number and the frame as an np.array
        """
        print("GET FRAME           ", end='\r')
        try:
            frame_num, source_queue = self.ref_queue.get(block=False)  # True, timeout=1 / 60)
            self.ref_queue.task_done()
            frame_num, frame = source_queue.get(block=False)  # True, timeout=1 / 60)
            source_queue.task_done()
        except queue.Empty:
            # print("queue_service: get_frame(): queue empty")
            return None, None

        return frame_num, frame

    def add_frame(self, frame_num: int, frame: np.array, detections: dict = None) -> None:

        print("ADD FRAME              ", end='\r')

        q = self.undet_queue
        name = 'no detection'

        # if detections are present, put in det queue and add
        # detections and monitored items
        if detections:
            q = self.det_queue
            name = 'detection'
            self._add_detection(detections)
            self._add_to_monitor(t=time.time(), detections=detections, f=frame)

        try:
            self.ref_queue.put((frame_num, q), block=True)  # True, timeout=1 / 60)
            q.put((frame_num, frame), block=True)  # True, timeout=1 / 60)
        except queue.Full as e:
            pass
            # print("queue_service: ref queue full: ", e)
            # drop frames when the queue is full
            # _ = self.ref_queue.get(block=False)  # True, timeout=1 / 60)
            # _ = q.get(block=False)
            # self.ref_queue.put((frame_num, q), block=False)
            # q.put((frame_num, frame), block=False)

    def get_detections(self) -> list:
        """get all detections from queue as a list"""
        print("GET ALL DETECTIONS   ", end='\r')
        det_list = []

        while not self.detections_queue.empty():
            det_list.append(self.detections_queue.get())
            self.detections_queue.task_done()

        return det_list

    def _add_detection(self, detections) -> None:
        """add a detection to detections queue. clear an item if queue is full."""
        # print("queue_service: adding to detections ...")
        print("ADD DETECTION         ", end='\r')
        try:
            self.detections_queue.put(detections, block=True, timeout=1 / 60)
        except queue.Full:
            # if full, remove an item to make room and add new item
            _ = self.detections_queue.get(block=False)  # True, timeout=1 / 60)
            self.detections_queue.task_done()
            self.detections_queue.put(detections)
        # print("queue_service: added to detections!")

    def get_monitored_item(self) -> (bool, float, set, np.array):
        """return item from monitored items queue"""
        print("GET MONITORED ITEM    ", end='\r')
        try:
            d_elems = self.mon_queue.get(block=True, timeout=1 / 60)  # need to allow pass in case of shutdown
            self.mon_queue.task_done()
            time_stamp = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(d_elems.get('t')))

            d_items = d_elems.get('d')

            return True, time_stamp, d_items, d_elems.get('f')

        except queue.Empty:
            return False, None, None, None

    def _add_to_monitor(self, t: time, detections: dict, f: np.array) -> None:
        """add to monitored items queue. monitor thread will determine if
        item needs to be monitored or not.  All detections will be put
        into this queue."""
        print("ADD TO MONITOR       ", end='\r')
        d_items = {d.get('name') for d in detections}  # make set of names
        # print("queue_service: adding to monitor ...")
        try:
            self.mon_queue.put({"t": t, "d": set(d_items), "f": f}, block=True, timeout=1 / 60)
        except queue.Full:
            # if full, remove an item to make room and add new item
            _ = self.mon_queue.get(block=False)  # True, timeout=1 / 60)
            self.mon_queue.task_done()
            self.mon_queue.put({"t": t, "d": set(d_items), "f": f})
        # print("queue_service: added to monitor!")

    # END - GET AND ADD FRAMES FROM/TO QUEUES ##################################

    def get_qsize(self, queue_name: str) -> int:
        if queue_name == 'ref_queue':
            return self.ref_queue.qsize()
        if queue_name == 'det_queue':
            return self.det_queue.qsize()
        if queue_name == 'undet_queue':
            return self.undet_queue.qsize()
        if queue_name == 'detections_queue':
            return self.detections_queue.qsize()
        if queue_name == 'mon_queue':
            return self.mon_queue.qsize()

    def clear(self, q: str):
        clear_me = None
        if q == 'ref_queue':
            clear_me = self.ref_queue
        if q == 'det_queue':
            clear_me = self.det_queue
        if q == 'undet_queue':
            clear_me = self.undet_queue
        if q == 'detections_queue':
            clear_me = self.detections_queue
        if q == 'mon_queue':
            clear_me = self.mon_queue

        with clear_me.mutex:
            while not clear_me.empty:
                _ = clear_me.get()
                clear_me.task_done()

    def clear_all_queues(self, ):
        for q in ('ref_queue',
                  'det_queue',
                  'undet_queue',
                  'detections_queue',
                  'mon_queue'):
            self.clear(q)

        print("Cleared all queues!")
