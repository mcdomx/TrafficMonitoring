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
    def __init__(self, name, tm):
        Thread.__init__(self, name, thread_mgr=tm)

    def run(self):

        self._running = True
        while self._running:

            time.sleep(60/self.tm.ps.DPM)  # need to pause to allow other threads to run
            success, time_stamp, d_items, image = self.tm.qs.get_monitored_item()

            if success and (d_items & self.tm.ps.MON_OBJS):
                cv2.imwrite(os.path.join(self.tm.ps.MON_DIR, "{}.png".format(time_stamp)), image)
