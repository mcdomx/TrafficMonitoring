import time
import datetime
import os
from collections import Counter
import json

from modules.threads.thread import Thread
from modules.timers.elapsed_time import ElapsedTime


def calc_avg_counts(minute_detections: list) -> dict:
    """
    Converts a minute of detections into a dictionary
    of items and their average counts.
    """
    counts = Counter()
    num_detections = len(minute_detections)

    # first convert each frame detection into counts
    for frame_detections in minute_detections:
        counts.update([d.get('name') for d in frame_detections])

    # then calculate the average
    counts = {k: v/num_detections for k, v in counts.items()}

    return counts


def log_counts(cap_time, counts, filepath):
    save_time = datetime.datetime(year=cap_time.year,
                                  month=cap_time.month,
                                  day=cap_time.day,
                                  hour=cap_time.hour,
                                  minute=cap_time.minute)

    # insert header for first record
    if not os.path.isfile(filepath):
        with open(filepath, 'w') as fp:
            fp.write("date_time|day_minute|object|count\n")

    with open(filepath, 'a') as fp:
        for k, v in counts.items():
            fp.write(str(save_time))
            fp.write('|')
            fp.write("{}".format(cap_time.hour * 60 + cap_time.minute))  # day_minute
            fp.write('|')
            fp.write(k)
            fp.write('|')
            fp.write("{}".format(round(v, 6)))
            fp.write('\n')


class LoggingThread(Thread):
    """
    Log detections to file.
    At each interval (usu. 1 second) detections are added to a list.
    This thread will convert that list into the averages for the
    logging period (usu. 1 minute).
    """

    def __init__(self, name: str, tm):
        self._elapsed_time = None
        Thread.__init__(self, name, thread_mgr=tm)

    def run(self):
        """
        go through detections list
        add detected items to dictionary
        """
        # clear any existing logging activity
        self.tm.qs.clear('detections_queue')

        # start timer
        self._elapsed_time = ElapsedTime()
        minute_counter = 0

        self._running = True

        while self._running:

            # loop till minute has elapsed
            while self._elapsed_time.get() - minute_counter < 60 and self._running:
                time.sleep(1)
            minute_counter = self._elapsed_time.get()

            # record time of count
            count_time = datetime.datetime.now()

            # get all detections from queue
            det_list = self.tm.qs.get_detections()

            # auto-throttle detection rate
            self.tm.ps.DPM = len(det_list)

            # convert detections to avg counts
            minute_averages = calc_avg_counts(det_list)

            # Log data to file
            if len(minute_averages) > 0:
                log_counts(count_time, minute_averages, self.tm.ps.LOG_FILEPATH)

            # log to console
            print("\n\t{}   # detections: {}".format(count_time, len(det_list)))
            print("\tAvg/Min: ", end='')
            for k, v in minute_averages.items():
                print("{}:{}".format(k, round(v, 2)), end='  ')
            print("")

            # emit
            minute_averages['time_stamp'] = '{:04}-{:02}-{:02} {:02}:{:02}:{:02}'.format(count_time.year,
                                                                                         count_time.month,
                                                                                         count_time.day,
                                                                                         count_time.hour,
                                                                                         count_time.minute,
                                                                                         count_time.second)

            self.tm.socketio.emit("update_log", json.dumps(minute_averages), broadcast=True)

