FROM tensorflow/tensorflow:1.13.2-py3-jupyter
#FROM tensorflow/tensorflow:1.15.0-py3-jupyter # lots fo depreciaton warnings - tls error exists
#FROM tensorflow/tensorflow:2.1.0rc2-gpu-py3-jupyter # DOESNT WORK

RUN apt-get update
RUN apt-get install -y libsm6 libxext6 libfontconfig1 libxrender1 wget
RUN apt-get install nano
RUN apt-get install -qqy x11-apps

RUN pip3 install --upgrade pip

# Download pre-trained models
CMD mkdir /app/backbone
WORKDIR /app/backbones
RUN wget https://github.com/OlafenwaMoses/ImageAI/releases/download/1.0/yolo.h5
RUN wget https://github.com/OlafenwaMoses/ImageAI/releases/download/1.0/yolo-tiny.h5

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip install -r requirements.txt
RUN pip3 install https://github.com/OlafenwaMoses/ImageAI/releases/download/2.0.3/imageai-2.0.3-py3-none-any.whl

# Copy python code and custom objects file
COPY ./capture_video.py .
COPY ./modules ./modules
COPY ./*.json ./

# Make a log and captured images directory
CMD mkdir /app/logdir
CMD mkdir /app/monitored_images

ENTRYPOINT ["python", "capture_video.py"]

