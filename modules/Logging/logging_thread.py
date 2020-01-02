import threading
import time
import datetime
import os
from collections import Counter
from modules.queue_service import QueueService
from modules.parameters import Params

p = Params()


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


def log_counts(cap_time, counts):
    save_time = datetime.datetime(year=cap_time.year,
                                  month=cap_time.month,
                                  day=cap_time.day,
                                  hour=cap_time.hour,
                                  minute=cap_time.minute)

    # insert header for first record
    if not os.path.isfile(p.LOG_FILEPATH):
        with open(p.LOG_FILEPATH, 'w') as fp:
            fp.write("date_time|day_minute|object|count\n")

    with open(p.LOG_FILEPATH, 'a') as fp:
        for k, v in counts.items():
            fp.write(str(save_time))
            fp.write('|')
            fp.write("{}".format(cap_time.hour * 60 + cap_time.minute))  # day_minute
            fp.write('|')
            fp.write(k)
            fp.write('|')
            fp.write("{}".format(round(v, 6)))
            fp.write('\n')


class LoggingThread(threading.Thread):
    """
    Log detections to file.
    At each interval (usu. 1 second) detections are added to a list.
    This thread will convert that list into the averages for the
    logging period (usu. 1 minute).
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.qs = QueueService()
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

            # loop till minute has elapsed
            while elapsed_time() - minute_counter < 60 and self.running:
                time.sleep(1)
            minute_counter = elapsed_time()

            # record time of count
            count_time = datetime.datetime.now()

            # get detections from queue
            det_list = []
            while not self.qs.detections_queue.empty():
                det_list.append(self.qs.detections_queue.get())

            # auto-throttle detection rate
            p.update_DPM(len(det_list))

            # convert detections to avg counts
            minute_averages = calc_avg_counts(det_list)

            # Log data to file
            if len(minute_averages) > 0:
                log_counts(count_time, minute_averages)

            # log to console
            print("\n\t{}   # detections: {}".format(count_time, len(det_list)))
            print("\tAvg/Min: ", end='')
            for k, v in minute_averages.items():
                print("{}:{}".format(k, round(v, 2)), end='  ')
            print("")

        print("Exited '{}'!".format(self.getName()))

    def stop(self):
        self.running = False
