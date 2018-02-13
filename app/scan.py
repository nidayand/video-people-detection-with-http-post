import numpy as np
import cv2
import video
from pushbullet import Pushbullet
import time
import os

# initialize the list of class labels MobileNet SSD was trained to
# detect, then generate a set of bounding box colors for each class
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person"]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

prototxt = "MobileNetSSD_deploy.prototxt.txt"
model = "MobileNetSSD_deploy.caffemodel"


class Detect:
    def __init__(self, api, conf, frames):
        self.pushbullet = Pushbullet(api)
        self.conf = conf
        self.frames = frames

        global prototxt, model

        print('loading model')
        self.net = cv2.dnn.readNetFromCaffe(prototxt, model)

    description = 'Scanning for a person and sends a pusbullet image if detected'
    author = 'Peter Gothager <pggithub@gothager.se'

    def run(self, movie, scewed=None):
        global CLASSES, COLORS

        # check that the file is not too big. Will check again
        # as this possibly captures continous saving
        try:
            if os.stat(movie).st_size/1024/1024 > int(os.getenv('MAX_SIZE', "20")):
                # too large file to process
                print('too large file to process. skipping. '+movie)
                return
        except:
            pass

        cam = None
        avail = False
        c = 0
        while not avail:
            if c > 30:
                print('it takes too long time to open the video (>60s). skipping analysis (exit)')
                return

            # open video stream
            cam = video.create_capture(movie)
            if cam.isOpened():
                avail = True
            else:
                c += 1
                time.sleep(2)

        print('movie is ready to be read!')

        # verifying again that the saved file did not exceed
        # during saving 20 MB
        try:
            if os.stat(movie).st_size/1024/1024 > int(os.getenv('MAX_SIZE', "20")):
                # too large file to process
                print('too large file to process. skipping. '+movie)
                return
        except:
            pass

        # picture with highest confidence will be sent
        highest_confidence = 0
        output_image = None

        while True:
            # dont analyze every frame. it will simply
            # take forever
            if self.frames > 1:
                for x in range(0, (self.frames-1)):
                    try:
                        ret, frame = cam.read()
                    except:
                        pass
            ret, frame = cam.read()
            if frame is None:
                break

            # as the movie is a bit scewed, correct it
            if (scewed):
                frame = cv2.resize(frame, scewed)

            # load the input image and construct an input blob for the image
            # by resizing to a fixed 300x300 pixels and then normalizing it
            # (note: normalization is done via the authors of the MobileNet SSD
            # implementation)
            (h, w) = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)

            # pass the blob through the network and obtain the detections and
            # predictions
            # print("[INFO] computing object detections...")
            self.net.setInput(blob)
            detections = self.net.forward()

            # loop over the detections
            for i in np.arange(0, detections.shape[2]):
                # extract the index of the class label from the `detections`,
                # then compute the (x, y)-coordinates of the bounding box for
                # the object
                idx = int(detections[0, 0, i, 1])

                # only continue if it is a person
                if idx > 16:
                    continue
                obj_type = CLASSES[idx]
                if obj_type == "person":
                    # extract confidence
                    confidence = detections[0, 0, i, 2]

                    # filter out for higher confidence than confidenceset var
                    if confidence > self.conf and confidence > highest_confidence:
                        # display prediction
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        (startX, startY, endX, endY) = box.astype("int")

                        label = "{}: {:.2f}%".format(CLASSES[idx], confidence * 100)
                        print("[INFO] {}".format(label))
                        cv2.rectangle(frame,
                                      (startX, startY),
                                      (endX, endY),
                                      COLORS[idx],
                                      2)
                        y = startY - 15 if startY - 15 > 15 else startY + 15
                        cv2.putText(frame,
                                    label,
                                    (startX, y),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    COLORS[idx],
                                    2)

                        # store the output image
                        output_image = frame
                        highest_confidence = confidence
        # send to pushbullet
        if highest_confidence > 0:
            cv2.imwrite("frame.jpg", output_image)
            with open("frame.jpg", "rb") as pic:
                file_data = self.pushbullet.upload_file(pic, "Person Detected")
            push = self.pushbullet.push_file(**file_data)
        cam.release()
