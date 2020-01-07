#!/usr/bin/env python
import os
import time

import numpy as np
from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import cv2
from PIL import Image

from modules.threads.thread_manager import ThreadManager
from modules.services.queue_service import QueueService
from modules.services.parameters import Params

# set global attributes
p = Params()
qs = QueueService()
app = Flask(__name__)
socketio = SocketIO(app)
thread_manager = ThreadManager(socketio)

# Check for environment variables
if not os.getenv("FLASK_APP"):
    raise RuntimeError("-- Environment variable FLASK_APP is not set")


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def add_overlay(frame: np.array, stats: dict) -> np.array:
    """
    Adds overly to current 'frame'.  Uses local variables
    stats and frame.  'stats' is a dictionary
    where keys are displayed statistics and values are the
    respective values.
    """
    # HELP MENU
    cv2.putText(frame, "{}".format("'q' - quit"),
                (10, frame.shape[0] - 10),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.4,
                color=(200, 0, 0),
                thickness=1)

    # STATISTICS
    # cv2.putText(frame, "{}".format("dpm: {}".format(round(capture_thread.get_dpm(), 1))),
    for i, (k, v) in enumerate(stats.items()):
        cv2.putText(frame, "{:6} : {}".format(k, round(v, 3)),
                    (frame.shape[1] - 100, frame.shape[0] - 10 - (i * 15)),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.4,
                    color=(200, 0, 0),
                    thickness=1)

    return frame


def get_frame(stats: dict = None) -> (int, np.array, float):
    frame_num, source_queue = qs.ref_queue.get()
    qs.ref_queue.task_done()
    frame_num, frame = source_queue.get()
    source_queue.task_done()

    # frame overlay
    if stats:
        frame = add_overlay(frame, stats)

    # pause extra to display captures
    f_delay = 0
    if source_queue is qs.det_queue:
        f_delay = .25

    return frame_num, frame, f_delay


def gen():
    """Video streaming generator function."""
    tmpfile = os.path.join(p.MON_DIR, "temp.jpg")
    base_delay = 0.05
    t_delay = base_delay
    stats = {}

    while thread_manager.all_running:

        stats.setdefault('dpm', round(p.DPM, 1))
        stats.setdefault('delay', t_delay)

        frame_num, frame, frame_delay = get_frame(stats)
        t_delay = 1 / (qs.ref_queue.qsize() + 2) + base_delay + frame_delay

        # convert to jpeg
        Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).save(tmpfile)
        with open(tmpfile, 'rb') as fp:
            frame = fp.read()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        time.sleep(t_delay)


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/toggle_stream')
def toggle_stream():
    """
    Turn stream off or on, depending on the current state
    :return: None
    """
    if thread_manager.all_running:
        thread_manager.terminate_threads()
        qs.clear_queues()
    else:
        thread_manager.start_threads()

    return render_template('index.html')


@socketio.on('connect')
def handle_startup():
    print("Socket connection is established!")


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)  # , threaded=True)  # , use_reloader=False)

