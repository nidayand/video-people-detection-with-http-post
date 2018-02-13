FROM python:3.6.4-slim
MAINTAINER Peter Gothager <pggithub@gothager.se>

RUN apt-get update && \
        apt-get install -y \
        build-essential \
        cmake \
        git \
        wget \
        unzip \
        yasm \
        pkg-config \
        libswscale-dev \
        libtbb2 \
        libtbb-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libjasper-dev \
        libavformat-dev \
        libpq-dev

RUN pip install numpy

WORKDIR /
ENV OPENCV_VERSION="3.4.0"
RUN wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip \
&& unzip ${OPENCV_VERSION}.zip \
&& mkdir /opencv-${OPENCV_VERSION}/cmake_binary \
&& cd /opencv-${OPENCV_VERSION}/cmake_binary \
&& cmake -DBUILD_TIFF=ON \
  -D BUILD_opencv_java=OFF \
  -D BUILD_NEW_PYTHON_SUPPORT=ON \
  -D WITH_OPENGL=ON \
  -D WITH_OPENMP=ON \
  -D WITH_OPENCL=ON \
  -D BUILD_DOCS=ON \
  -D WITH_EIGEN=ON \
  -D BUILD_TEST=ON \
  -D WITH_GTK=ON \
  -D WITH_TBB=ON \
  -D WITH_V4L=ON \
  -D WITH_QT=OFF \
  -D CMAKE_BUILD_TYPE=RELEASE \
  -D CMAKE_INSTALL_PREFIX=$(python3.6 -c "import sys; print(sys.prefix)") \
  -D PYTHON_EXECUTABLE=$(which python3.6) \
  -D PYTHON_INCLUDE_DIR=$(python3.6 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
  -D PYTHON_PACKAGES_PATH=$(python3.6 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") .. \
&& make install \
&& rm /${OPENCV_VERSION}.zip \
&& rm -r /opencv-${OPENCV_VERSION}

RUN pip install pushbullet.py
RUN pip install requests

# Set the working directory to /app
WORKDIR /app

ADD ./app /app

# Make port 80 available to the world outside this container
EXPOSE 8080

# Run app.py when the container launches
CMD ["python", "service.py"]
