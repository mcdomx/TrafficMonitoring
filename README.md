# Traffic Detection (v3.0)

Traffic Detection is designed to capture a stream of video, perform object detection, and display the video stream with detections as well as capture statistics of items detected.  Additionally, Traffic Detection will save detection statistics to a CSV file and supports saving captured frames where selected objects have been detected.

Any standard browser can be used as the front end to display the modified video stream as well as captured statistics.  This browser-based front-end relies on Flask to deliver web pages.  

The program is intended to be run inside of a Docker container.  Docker must be installed and running on the host machine in order to execute the program.

Configuration of a stream is done using a YAML file. A default YAML file is provided as an example.  The Docker configuration elements are set in a separate docker-compose.yaml file.  The stream configuration's YAML file is identified in the docker-compose file.

The video source can be a local video file, a web stream or a local webcam.  For YouTube streams, the YouTube stream ID can be used (e.g. - '1EiC9bvVGnk') instead of the full URL.  Other video sources require a fully qualified URL.  Host-based cams are supported by supplying the integer identifier (usu. '0' for the user-facing camera on a computer with a cam).

The default image detectector relies on an ImageAI implementation of instance detection. (
<a href=https://github.com/OlafenwaMoses/ImageAI>https://github.com/OlafenwaMoses/ImageAI</a>)

The code has been written to allow other models to be used by extending classes and implementing defined methods for the new class.

*NOTE: This implementation has only be tested to run on an OSX host computer.*

### Setup and Execution
1. Clone this repository.
2. Start docker on the host machine
3. Build and execute the Docker container from the project root:

    `docker-compose s up --build`

This will build and execute the container.  You can run without building by leaving off the `--build` switch.
	
Once started, the site can be reached at: 127.0.0.1:5000


### Stream YAML Configuration
A folder called 'config' is intended to store YAML files that represent a stream and it's respective configuration.  The default YAML configuration:

    CAM_STREAM: 1EiC9bvVGnk
    LOGGING: true
    LOG_FILEPATH: ./logs/files/camlogs.txt
    DETECTION: true
    DETECTOR_NAME: imageai
    DETECTOR_MODEL: yolo
    DPM: 20
    DISPLAY_FPS: 30
    MONITORING: true
    MON_DIR: ./logs/images
    MON_OBJS:
      - person
    DET_OBJS:
      - person
      - car
      - bus
    BASE_DELAY: 0.045



|  Variable Name    | Type        | Description      | 
| :---------------- | :---------- | :--------------- | 
| CAM_STREAM        | String      | URL of the webcam stream.  Can also be a YouTube video.  The YouTube path of 11-digit ID can be used. A numeric value is cast to an integer so "0" becomes 0 and uses the computer's built-in camera.|
| LOGGING           | Bool(String)| "true" or "false".  Whether or not to log detections to output file.
| LOG_FILEPATH      | String      | The local path where log file should be saved.  Ignored if LOGGING is "false".
| DETECTION         | Bool(String)| "true" of "false".  Whether or not to perform inference.  If "false", real-time video stream is displayed with no inference overlays.
| DETECTOR_NAME     | String      | Name of detector to use.  See 'Detectors' section for supported Detectors.
| DETECTOR_MODEL    | String      | Name of the detector's model use for inference. See 'Detectors' section for supported models.
| DPM               | int(String) | Detections per Minute.  This value will auto-adjust based on the local computer's ability to process.  This variable is best left unchanged.
| DISPLAY_FPS       | int(String) | The displayed frame rate. Set to the video's FPS if the DISPLAY_FPS is greater than the video.  Best to leave default value of '30'.
| MONITORING        | Bool(String)| 'true of 'false'.  Will save images of captured objects according to object names listed in the `MON_OBJS` variable below.
| MON_DIR           | String      | Relative filepath of the directory where monitored object frame images are saved. 
| MON_OBJS          | YAML List   | Each item in the list will be monitored saving the objects frame image in the `MON_DIR` directory.  Objects can be added and removed in the Logging section of the front-end.
| DET_OBJS          | YAML List   | Only items in this list are detected.  These items are shown in the overlay of detections and logged.  Objects can be added and removed in the Logging section of the front-end.
| BASE_DELAY        | Float       | This value will smooth the video display.  This value can be adjusted in the front-end interface in the Video Controls section.  


### Detectors
Currently, only the "imageai" detector is supported:

|  Detector Name    | Type              | Supported models      |
| :---------------- | :---------------- | :-------------------- | 
| 'imageai'         | Object Detection  | 'yolo', 'tinyyolo'
	

### Logging
The application supports logging to the terminal by default.  Application-wide formatting is used to streamline logging output.  The application also supports a javascript driven logging for debugging.