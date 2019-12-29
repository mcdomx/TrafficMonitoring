import threading
import queue
import cv2
import json


class Monitor(threading.Thread):
    """
    Thread will monitor a queue where each detection is placed.
    If an item in the detection is in the mon_list,
    save the image.
    """
    def __init__(self, mon_queue: queue.Queue):
        threading.Thread.__init__(self)
        self.mon_queue = mon_queue  # (time, detections, image)
        self.running = False
        print("Monitoring:   ON")

    # @staticmethod
    # def get_monitorlist(self, file_name="./monitor_list.txt") -> set:
    #     with open(file_name, 'r') as fp:
    #         filelines = fp.readlines()
    #     return {line.strip() for line in filelines}

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
                time_stamp, detections, image = self.mon_queue.get(block=True, timeout=1/60) #
                # for i, item in enumerate(x):
                #     print("{}: {}".format(i, item))

                d_items = {d['name'] for d in detections}

                if len(d_items & mon_list) > 0:
                    cv2.imwrite("./logdir/{}.png".format(time_stamp), image)

            except queue.Empty:
                continue

    def stop(self):
        self.running = False
