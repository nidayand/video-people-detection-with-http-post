FROM nidayand/video-opencv-pushbullet

RUN pip install flask
RUN pip install requests --upgrade

# Set the working directory to /app
WORKDIR /app

ADD ./app /app

# Make port 80 available to the world outside this container
EXPOSE 8080

# Run app.py when the container launches
CMD ["python", "-u", "service.py"]
