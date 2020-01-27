import time
import datetime
import os
import threading
from collections import Counter
import json
import logging

from flask_socketio import SocketIO

from modules.services.service import Service
from modules.timers.elapsed_time import ElapsedTime

logger = logging.getLogger('app')


class LoggingService(Service, threading.Thread):
    """
    Log detections to file.
    After each detection, the detected items are logged.  After the
    logging interval has expired, a summary of the items logged
    is calculated and the averages over the time period are stored.

    This thread will convert that list into the averages for the
    logging period (usu. 1 minute).

    Since this process must count detection statistics on a fixed interval,
    this process is run as a thread to ensure that it calculates summaries
    after the specified logging period and not only after a detection has
    been made.
    """

    def __init__(self,
                 name: str,
                 file_path: str,
                 detection_rate: float,
                 socketio: SocketIO):
        Service.__init__(self, name)
        threading.Thread.__init__(self)
        self.name = name
        self._elapsed_time = None
        self._detections = None
        self._log_filepath = file_path
        self._dpm = detection_rate
        self._socketio = socketio

    # GETTERS AND SETTERS
    @property
    def dpm(self):
        return self._dpm

    @dpm.setter
    def dpm(self, val):
        self._dpm = val

    @property
    def log_filepath(self):
        return self._log_filepath

    @log_filepath.setter
    def log_filepath(self, val):
        self._log_filepath = val
    # END GETTERS AND SETTERS

    def start(self):
        self._running = True
        threading.Thread.start(self)

    def log_detections(self, detections: list):
        """
        Adds a list of detections that will be summarized when an
        interval period has expired.
        :return:
        """
        if not self._detections:
            self._detections = []
        self._detections.append(detections)

    def run(self):
        """
        go through detections list
        add detected items to dictionary
        """
        # clear any existing logging activity
        self._detections = None

        # start timer
        self._elapsed_time = ElapsedTime()
        minute_counter = 0

        self._running = True

        logger.info("Started logging loop!")

        while self._running:

            # loop till minute has elapsed
            # while self._elapsed_time.get() - minute_counter < 60 and self._running:
            time.sleep(60)
            # minute_counter = self._elapsed_time.get()

            if not self._detections:
                logger.info("No detections")
                continue

            logger.info("Counting detections")
            # record time of count
            count_time = datetime.datetime.now()

            # get all detections from list and clear list
            det_list = self._detections.copy()
            self._detections = None

            # auto-throttle detection rate
            self.dpm = len(det_list)

            # convert detections to avg counts
            minute_averages = _calc_avg_counts(det_list)

            # Log data to file
            if len(minute_averages) > 0:
                _log_counts(count_time, minute_averages, self.log_filepath)

            # log to console
            logger.info("Detections: {}".format(len(det_list)))
            output = "--> Avg/Min: "
            for k, v in minute_averages.items():
                output += "{}:{}  ".format(k, round(v, 2))
            logger.info("{}".format(output))

            # emit
            minute_averages['time_stamp'] = '{:04}-{:02}-{:02} {:02}:{:02}:{:02}'.format(count_time.year,
                                                                                         count_time.month,
                                                                                         count_time.day,
                                                                                         count_time.hour,
                                                                                         count_time.minute,
                                                                                         count_time.second)

            self._socketio.emit("update_log", json.dumps(minute_averages), broadcast=True)


def _calc_avg_counts(minute_detections: list) -> dict:
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
    counts = {k: v / num_detections for k, v in counts.items()}

    return counts


def _log_counts(cap_time, counts, filepath):
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
