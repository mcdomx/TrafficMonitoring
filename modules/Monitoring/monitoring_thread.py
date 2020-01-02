import threading
import queue
import cv2
import json
from modules.queue_service import QueueService


class Monitor(threading.Thread):
    """
    Thread will monitor a queue where each detection is placed.
    If an item in the detection is in the mon_list,
    save the image.
    """
    def __init__(self):  # , mon_queue: queue.Queue):
        threading.Thread.__init__(self)
        self.qs = QueueService()
        self.running = False
        print("monitoring:   ON")

    @staticmethod
    def get_monitorlist(file_name="monitor_objects.json") -> set:
        with open(file_name, 'r') as fp:
            mon_dict = json.load(fp)

        return {k.strip() for k, v in mon_dict.items() if v == 'valid'}

    def run(self):

        mon_list = self.__class__.get_monitorlist()

        print("Monitored items: ")
        for i in mon_list:
            print("\t{}".format(i))

        self.running = True
        while self.running:
            try:
                time_stamp, detections, image = self.qs.mon_queue.get(block=True, timeout=1/60)
                d_items = {d.get('name') for d in detections}

                # if an item is detected and being monitored
                if len(d_items & mon_list) > 0:
                    cv2.imwrite("./logdir/{}.png".format(time_stamp), image)

            except queue.Empty:
                continue

    def stop(self):
        self.running = False
