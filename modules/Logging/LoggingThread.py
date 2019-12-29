import threading
import time
import datetime
import os


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


def log_counts(cap_time, log_filepath, counts):
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


class LoggingThread(threading.Thread):
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
            if cur_dpm > act_dpm and cur_dpm > 10:  # throttle down - never go below 10
                self.read_thread.set_dpm(act_dpm + int((cur_dpm - act_dpm) / 2))
            else:  # throttle up
                self.read_thread.set_dpm(act_dpm + 1)

            # convert detections to avg counts
            minute_counts = convert_detections_to_avg_counts(det_list)

            # Log data to file
            if len(minute_counts) > 0:
                log_filepath = os.getenv("LOG_FILEPATH", "./logdir/camlogs.txt")
                log_counts(cap_time, log_filepath, minute_counts)

            print("\n\t{}   # detections: {}".format(cap_time, len(det_list)))
            print("\tAvg/Min: ", end='')
            for k, v in minute_counts.items():
                print("{}:{}".format(k, round(v, 2)), end='  ')
            print("")

        print("Exited '{}'!".format(self.getName()))

    def stop(self):
        self.running = False
