import queue
import os
import time

import cv2

from modules.threads.thread import Thread


class MonitorThread(Thread):
    """
    Thread will monitor a queue where each detection is placed.
    If an item in the detection is in the mon_list,
    save the image.
    """
    def __init__(self, name):
        Thread.__init__(self, name)

    def run(self):

        self._running = True
        while self._running:
            try:
                d_elems = self._qs.mon_queue.get(block=True, timeout=1/60)  # need to allow pass in case of shutdown
                time_stamp = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(d_elems.get('t')))
                detections = d_elems.get('d')
                image = d_elems.get('f')

                d_items = {d.get('name') for d in detections}

                # if an item is detected and being monitored
                if d_items & self._p.MON_OBJS:
                    cv2.imwrite(os.path.join(self._p.MON_DIR, "{}.png".format(time_stamp)), image)

            except queue.Empty:
                continue

