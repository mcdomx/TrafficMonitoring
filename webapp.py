#!/usr/bin/env python
import os
import time
import logging

from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import cv2

from modules.services.service_manager import ServiceManager
from modules.timers.elapsed_time import ElapsedTime


logger = logging.getLogger('app')
formatter = logging.Formatter('%(asctime)-19s - %(module)-15s - %(levelname)s - %(message)s')
logger.setLevel(level=logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)


# set global attributes
app = Flask(__name__)
if not os.getenv("FLASK_APP"):
    raise RuntimeError("-- Environment variable FLASK_APP is not set")

socketio = SocketIO(app)

# setup a thread manager
sm = ServiceManager(socketio)

# TEMP - FOR DEVELOPMENT
sm.config.BASE_DELAY = .045


@app.route('/')
def index():
    """
    Video streaming home page.
    """
    if not sm.all_running:
        sm.start_all_services()
    return render_template('index.html',
                           trained_objs=sm.get_trained_objects(),
                           mon_objs=sm.config.MON_OBJS,
                           det_objs=sm.config.DET_OBJS)


def gen():
    """Video streaming generator function."""

    logger.info("Started display loop!")
    elapsed_time = ElapsedTime()

    while sm.all_running:

        # micro-nap until the display rate is reached
        sleep_time = sm.config.BASE_DELAY
        print("SLEEPING {:04} {}              ".format(sleep_time, sm.get_queue_size()), end='\r')
        time.sleep(sleep_time)
        # print("DONE SLEEPING               ", end='\r')

        success, frame = sm.get_frame()

        # if queue was empty, skip
        if not success:
            print("EMPTY QUEUE               ", end='\r')
            continue

        # convert to jpeg
        print("CONVERT TO JPEG         ", end='\r')
        frame = cv2.imencode('.jpg', frame)[1].tobytes()

        print("YIELD              ", end='\r')
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        print("YIELDED              ", end='\r')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/toggle_stream')
def toggle_stream():
    """
    Toggle the streaming display.  Logging and monitoring should continue.
    :return: None
    """
    sm.toggle_all()
    return '', 204


@app.route('/toggle_thread/<thread>')
def toggle_thread(thread: str):
    """Toggle running status of thread name from argument"""
    sm.toggle(thread)
    return '', 204


@app.route('/change_delay/<direction>')
def change_delay(direction: str):

    if direction == 'increase':
        sm.config.BASE_DELAY += .002
        logger.info(f"new delay: {sm.config.BASE_DELAY}")

    if direction == 'decrease':
        sm.config.BASE_DELAY = max(0, sm.config.BASE_DELAY - .002)
        logger.info(f"new delay: {sm.config.BASE_DELAY}")

    return '', 204


@app.route('/toggle_monitem/<log_object>')
def toggle_monitem(log_object: str):
    logger.info("MONITOR LOGITEM UPDATE: {}".format(log_object))
    if sm.config.is_monitored(log_object):
        sm.config.del_mon_obj(log_object)
    else:
        sm.config.add_mon_obj(log_object)
    return '', 204


@app.route('/toggle_detitem/<log_object>')
def toggle_detitem(log_object: str):
    logger.info("DETECTION LOGITEM UPDATE: {}".format(log_object))
    if sm.config.is_detected(log_object):
        sm.config.del_det_obj(log_object)
    else:
        sm.config.add_det_obj(log_object)
    return '', 204


@socketio.on('connect')
def handle_startup():
    logger.info("Socket connection is established on server!")


if __name__ == '__main__':
    sm.stop_all_services()  # stop all in case of flask restart
    sm.add_all_services()  # services are added here and started when page is loaded
    socketio.run(app, host='0.0.0.0', port=5000)
