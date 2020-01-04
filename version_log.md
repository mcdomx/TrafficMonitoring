# Traffic Detection Version Log
-
### v1.0 - Init Relase

Features:

* Runs in Docker
* Includes a Jupyter Notebook for development
* Supports Google Streams and Video
* Supports web

### v2.0 - Update

Changes:

* better use of object oriented design with classes and separation of concerns
* significant refactoring for performance improvements
* created a singleton Params class for application paramters and variables
* creates 'SHOW_VIDEO' mode to turn video preview on or off (setting to 'True' or 'False')
* enable snap shots based on conditional presence of object, "monitoring"
* added support for various new docker env variables 

### v3.0 (in process)- flask web page

* use browser to display video
https://blog.miguelgrinberg.com/post/video-streaming-with-flask
* enable auto frame speed for displayed video previews
