import queue


class QueueService:
    """
    Singleton class.
    Holds queues necessary for video capture, inference and display.

    # 5 queues are used.
            # 'det_queue'   : Holds tuples for each frame with detected objects.
            #                 tuple(frame_num, frame_image)
            # 'undet_queue' : Holds tuples for each frame with no detected objects.
            #                 tuple(frame_num, frame_image)
            # 'ref_queue'   : Holds tuples for each frame captured.
            #                 tuple(frame_num, queue_of_frame_image)
            # 'detections_queue' : Holds lists of detected objects from each detected frame
            # 'mon_queue'   : Holds items in each detection that will be checked for monitoring
    """
    singleton = None

    def __new__(cls, buffer_size: int = 256):
        if cls.singleton is None:
            cls.singleton = cls.__Singleton(buffer_size)
        elif buffer_size != cls.singleton.get_buffersize():
            print("Buffer size cannot be changed: {}".format(cls.singleton.buffer_size))
        return cls.singleton

    class __Singleton:
        def __init__(self, buffer_size: int = 256):
            self.buffer_size = buffer_size
            self.ref_queue = queue.Queue(buffer_size)  # includes frame num and queue to get frame from
            self.det_queue = queue.Queue(buffer_size)  # includes frames with processed detections
            self.undet_queue = queue.Queue(buffer_size)  # includes frame without detections
            self.detections_queue = queue.Queue()  # includes detections for the logging interval period
            self.mon_queue = queue.Queue()  # used to monitor detections (time, detections, image)

        def get_buffersize(self) -> int:
            return self.buffer_size

        def clear_queues(self):
            for q in (self.ref_queue,
                      self.det_queue,
                      self.undet_queue,
                      self.detections_queue,
                      self.mon_queue):
                self.clear_queue(q)

        @staticmethod
        def clear_queue(q: queue.Queue):
            with q.mutex:
                q.queue.clear()

        @staticmethod
        def resize_queue(q: queue.Queue, new_size: int):
            with q.mutex:
                new_q = queue.Queue(new_size)
                while q.not_empty:
                    new_q.put(q.get())
                q = new_q
