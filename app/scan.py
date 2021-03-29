import numpy as np
import cv2
import video
import time
import os, json
import requests

# initialize the list of class labels MobileNet SSD was trained to
# detect, then generate a set of bounding box colors for each class
CLASSES = [
    "background",
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
]
IGNORE = set(
    [
        "background",
        "aeroplane",
        "bicycle",
        "bird",
        "boat",
        "bottle",
        "bus",
        "car",
        "cat",
        "chair",
        "cow",
        "diningtable",
        "dog",
        "horse",
        "motorbike",
        "pottedplant",
        "sheep",
        "sofa",
        "train",
        "tvmonitor",
    ]
)
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

prototxt = "MobileNetSSD_deploy.prototxt.txt"
model = "MobileNetSSD_deploy.caffemodel"


class Detect:
    def __init__(self, dparams):
        self.urlpath = dparams["urlpath"]
        self.frames = dparams["frames"]
        self.conf = dparams["conf"]
        self.good_enough_conf = dparams["good_enough_conf"]
        self.width_person = dparams["width_person"]
        self.height_person = dparams["height_person"]
        self.width = dparams["width"]
        self.height = dparams["height"]
        self.ratio = dparams["ratio"]
        self.dparams = dparams

        global prototxt, model

        print("loading model")
        self.net = cv2.dnn.readNetFromCaffe(prototxt, model)

    description = "Scanning for a person and sends an image if detected"
    author = "Peter Gothager <pggithub@gothager.se"

    def run(self, movie, scewed=None):
        global CLASSES, COLORS

        # check that the file is not too big. Will check again
        # as this possibly captures continous saving
        try:
            if os.stat(movie).st_size / 1024 / 1024 > int(os.getenv("MAX_SIZE", "20")):
                # too large file to process
                print("too large file to process. skipping. " + movie)
                return
        except:
            pass

        cam = None
        avail = False
        c = 0
        while not avail:
            if c > 30:
                print(
                    "it takes too long time to open the video (>60s). skipping analysis (exit)"
                )
                return

            # open video stream
            cam = video.create_capture(movie)
            if cam.isOpened():
                avail = True
            else:
                c += 1
                time.sleep(2)

        print("movie is ready to be read!")

        # verifying again that the saved file did not exceed
        # during saving 20 MB
        try:
            if os.stat(movie).st_size / 1024 / 1024 > int(os.getenv("MAX_SIZE", "20")):
                # too large file to process
                print("too large file to process. skipping. " + movie)
                return
        except:
            pass

        # picture with highest confidence will be sent
        highest_confidence = 0
        person_width = 0
        person_height = 0
        output_image = None
        output_ratio = 0

        while True:
            # dont analyze every frame. it will simply
            # take forever
            if self.frames > 1:
                for x in range(0, (self.frames - 1)):
                    try:
                        ret, frame = cam.read()
                    except:
                        pass
            ret, frame = cam.read()
            if frame is None:
                break

            # as the movie is a bit scewed, correct it
            if scewed:
                frame = cv2.resize(frame, scewed)

            # load the input image and construct an input blob for the image
            # by resizing to a fixed 300x300 pixels and then normalizing it
            # (note: normalization is done via the authors of the MobileNet SSD
            # implementation)
            (h, w) = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(
                cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5
            )

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
                if idx < 0 or CLASSES[idx] in IGNORE:
                    continue

                # extract confidence
                confidence = detections[0, 0, i, 2]

                # filter out for higher confidence than confidenceset var
                if confidence > self.conf and confidence > highest_confidence:
                    # display prediction
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")

                    # check size of person
                    person_width = int((endX - startX) / self.width * 100)
                    person_height = int((endY - startY) / self.height * 100)

                    if self.width_person > 0 or self.height_person > 0:
                        if self.ratio > 0:
                            currentRatio = person_height / person_width
                            compareRatio = self.height_person / self.width_person
                            compareValue = currentRatio / compareRatio
                            if compareValue < 1:
                                compareValue = 1 - compareValue
                            else:
                                compareValue = compareValue - 1
                            compareValue = int(compareValue * 100)
                            if compareValue > self.ratio:
                                # Ration height/width differs too much. Skip
                                continue
                            output_ratio = compareValue

                        if person_width > self.width_person:
                            continue
                        if person_height > self.height_person:
                            continue

                    label = "{}: {:.2f}%".format(CLASSES[idx], confidence * 100)
                    print("[INFO] {}".format(label))
                    cv2.rectangle(frame, (startX, startY), (endX, endY), COLORS[idx], 2)
                    y = startY - 15 if startY - 15 > 15 else startY + 15
                    cv2.putText(
                        frame,
                        label,
                        (startX, y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        COLORS[idx],
                        2,
                    )

                    # store the output image
                    output_image = frame
                    highest_confidence = confidence

                # DETECTIONS IN FRAME: Check if higher than "good_enough_conf"
                if highest_confidence >= self.good_enough_conf:
                    break

            # WHILE: Check if higher than "good_enough_conf"
            if highest_confidence >= self.good_enough_conf:
                break

        # send to URL path
        if highest_confidence > 0:
            # save image temporarily
            cv2.imwrite("frame.jpg", output_image)

            # result
            res = {
                "success": True,
                "confidence": str(highest_confidence),
                "width": person_width,
                "height": person_height,
                "ratio_diff": output_ratio,
                "comment": "Person was found",
                "params": json.dumps(self.dparams)
            }

            # post to urlpath
            with open("frame.jpg", "rb") as pic:
                r = requests.post(
                    self.urlpath, data=res, files={"file": ("image.jpg", pic, "image/jpg")}
                )

            return res
        else:
            return {"success": False, "comment": "No person found"}

        cam.release()
