# Traffic Detection (v3.0) - UNDER DEVELOPMENT

Traffic Detection will capture detected images from a video stream.  The video stream will be displayed in a python image window while the program is running.  The program will detect images at an adjusted rate based on the computer's ability to handle detections.  Detections can be logged to a CSV file.  

A support Jupyter notebook is included for development, but the program is intended to be run in a Dokcer container.

The video source can be a local video file, a web stream or a local webcam.  The video source is set when running the Docker image that this program is intended to be run in.

This project relies on an ImageAI implementation of instance detection. (
<a href=https://github.com/OlafenwaMoses/ImageAI>https://github.com/OlafenwaMoses/ImageAI</a>)


*NOTE: This implementation has only be tested to run on an OSX host computer.*

### Setup and Exection

If you have already setup XServer and socat, you can skip to step 4.

**1.** Set local IP reference

	export LOCALIP=<local IP address>
<br>	

**2.** Install xQuartz and run XServer
	
	brew cask install xQuartz
ref:
<a href=https://cuneyt.aliustaoglu.biz/en/running-gui-applications-in-docker-on-windows-linux-mac-hosts/>https://cuneyt.aliustaoglu.biz/en/running-gui-applications-in-docker-on-windows-linux-mac-hosts/</a>
	
Run XServer
	
	xhost +"local ipaddress"
<br>
**3.** Install socat<br>
	Socat acts as a bridge between docker and the host system.
	
	brew install socat	
<br>
	Setup bridge:
	
	socat TCP-LISTEN:6000,reuseaddr,fork UNIX-CLIENT:\"$DISPLAY\" &

ref: <a href=https://cntnr.io/running-guis-with-docker-on-mac-os-x-a14df6a76efc>https://cntnr.io/running-guis-with-docker-on-mac-os-x-a14df6a76efc
</a>


<br>

**4.** Build and run the docker image from the root of the project directory where the `Docker` and this README.md files are located.

If Xserver and socat are already installed, you can start here.  Make sure that xserver is running and that your localIP is saved as an environment variable:

	export LOCALIP=<local IP address>
	xhost +$LOCALIP
	

Now build the docker container and run:

	docker build -t tf_detection .
	docker run -u $(id -u):$(id -g) -it --name traffic_monitor --net=host --rm -e DISPLAY=$LOCALIP:0  -e CAM_STREAM="0" -v /tmp/.X11-unix:/tmp/.X11-unix:ro -v "$PWD"/logs:/app/logs tf_detection
	
to run with flask:

	docker run -it --name traffic_monitor --rm -e CAM_STREAM="0" -v "$PWD"/logs:/app/logs -p 5000:5000 tf_detection

flask site can be reached at: 127.0.0.1:5000

Supported environment variables:<br>

|  Variable Name    | Type        | Usage Example    | Description      | 
| :---------------- | :---------- | :--------------- | :--------------- | 
| CAM_STREAM        | String      | -e CAM\_STREAM='http://pidev1.local:8080/?action=stream'<br>-e CAM\_STREAM='https://www.youtube.com/1EiC9bvVGnk'<br>-e CAM\_STREAM='1EiC9bvVGnk'<br>-e CAM_STREAM="0"| URL of the webcam stream.  Can also be a YouTube video.  The YouTube path of 11-digit ID can be used. A numeric value is cast to an integer so "0" becomes 0 and uses the computer's built-in camera.|
| LOGGING           | Bool(String)| -e LOGGING="True"      | "True" or "False".  Default="False.   Whether or not to log detections to output file.
| LOG_FILEPATH      | String      | -e LOG_FILEPATH="./logs/files/camlogs.txt"| The local path where log file should be saved.  Ignored if LOG_STREAM is "False".
| DETECTION         | Bool(String)| -e DETECTION="True"       | "True" of "False".  Whethre or not to perform inference.  If "False", real-time video stream is displayed with no inference overlay.
| DETECTOR_NAME          | String      | -e DETECTOR_NAME="imageai"       | Name of detector to use.  Default 'imageai'.  Currently only 'imageai' is supported.
| DETECTOR_MODEL             | String      | -e DETECTOR\_MODEL ="tinyyolo" <br> -e DETECTOR\_MODEL ="yolo"       | The name of the model to be used for inference. "yolo" is default. Only "yolo" and "tinyyolo" are supported.
| DPM               | int(String) | -e DPM="20"       | Detections per Minute.  Default is 20.  Value will auto-adjust based on the local computer's ability to process.
| DISPLAY_FPS       | int(String) | -e DISPLAY_FPS ="30"       | The displayed frame rate.  Default is "30".  Will be set to the video's FPS if the DISPLAY_FPS is greater than the video.
| MONITORING        | Bool(String)| -e MONITORING="True" | Default="True". Will save images of captured objects according to object names saved in the `monitor_list.txt` file.
| MON_DIR        | String | -e MON_DIR="./logs/images" | Default="./logs/images". Directory where images of monitored items are saved.
| SHOW_VIDEO        | Bool(String)| -e SHOW_VIDEO="True" | Default="True". Will save display video stream including detection overlays.


		

	
<br>
### Stopping Detection

A python video window will appear showing the video stream with object insantance enclosed in bounding boxes.  Press 'q' to stop the video process.

### Customize Detected Objects <br>
The file `custom_objects.json` is read used by the detector to determine which objects to detect and which to ignore.  You can manually set these to `valid` and `invalid` in the file.  Make sure to edit the file in an ASCII reader.
