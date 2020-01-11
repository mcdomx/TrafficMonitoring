#!/usr/bin/env python
import os
import time

from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import cv2

from modules.threads.thread_manager import ThreadManager

# set global attributes
app = Flask(__name__)
if not os.getenv("FLASK_APP"):
    raise RuntimeError("-- Environment variable FLASK_APP is not set")

socketio = SocketIO(app)

# setup thread manager
tm = ThreadManager(socketio)

# TEMP - FOR DEVELOPMENT
tm.ps.BASE_DELAY = .025


@app.route('/')
def index():
    """
    Video streaming home page.
    """
    if not tm.all_running:
        tm.start_all_threads()
    return render_template('index.html')


def gen():
    """Video streaming generator function."""

    print("Started display loop!")

    while tm.all_running:

        time.sleep(tm.ps.BASE_DELAY)

        frame_time, frame = tm.qs.get_frame()

        # if queue was empty, skip
        if not frame_time:
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
    Turn all threads on or off
    :return: None
    """
    tm.toggle_all()
    return '', 204


@app.route('/toggle_thread/<thread>')
def toggle_thread(thread: str):
    """Toggle running status of thread name from argument"""
    print("Toggling: ", thread)
    tm.toggle(thread)

    return '', 204


@app.route('/change_delay/<direction>')
def change_delay(direction: str):

    if direction == 'increase':
        tm.ps.BASE_DELAY += .002
        print(f"new delay: {tm.ps.BASE_DELAY}")

    if direction == 'decrease':
        tm.ps.BASE_DELAY = max(0, tm.ps.BASE_DELAY - .002)
        print(f"new delay: {tm.ps.BASE_DELAY}")

    return '', 204


@socketio.on('connect')
def handle_startup():
    print("Socket connection is established on server!")


if __name__ == '__main__':
    tm.stop_all_threads()
    tm.add_all_threads()
    socketio.run(app, host='0.0.0.0', port=5000)
