#!/usr/bin/env python
from __future__ import print_function

import numpy as np
import cv2
import argparse
import video
from pushbullet import Pushbullet

prototxt = "MobileNetSSD_deploy.prototxt.txt"
model = "MobileNetSSD_deploy.caffemodel"
confidenceset = 0.40
check_every_x_frame = 5
api_key = "o.8CVJHMxyRr6zyR753AGIDENm8H3wMjyn"

ap = argparse.ArgumentParser()
ap.add_argument("-m", "--movie", required=True,
	help="path to input movie")
args = vars(ap.parse_args())

# initialize the list of class labels MobileNet SSD was trained to
# detect, then generate a set of bounding box colors for each class
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
	"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
	"dog", "horse", "motorbike", "person"]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

# load our serialized model from disk
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe(prototxt, model)

# open video stream
cam = video.create_capture(args["movie"])

# initiate pushbullet
pb = Pushbullet(api_key)

# save only the highest confidence image
highest_confidence = 0
while True:
	# dont analyze every frame. it will simply
	# take forever
	if check_every_x_frame > 1:
		for x in range (0, (check_every_x_frame - 1)):
			try:
				ret, frame = cam.read()
			except:
				pass
	ret, frame = cam.read()
	if frame is None:
		break

	# as the movie is a bit scewed, correct it
	frame = cv2.resize(frame, (533, 400))

	# load the input image and construct an input blob for the image
	# by resizing to a fixed 300x300 pixels and then normalizing it
	# (note: normalization is done via the authors of the MobileNet SSD
	# implementation)
	(h, w) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)

	# pass the blob through the network and obtain the detections and
	# predictions
	# print("[INFO] computing object detections...")
	net.setInput(blob)
	detections = net.forward()

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

			#filter out for higher confidence than confidenceset var
			if confidence > confidenceset and confidence > highest_confidence:
				# display prediction
				box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
				(startX, startY, endX, endY) = box.astype("int")

				label = "{}: {:.2f}%".format(CLASSES[idx], confidence * 100)
				print("[INFO] {}".format(label))
				cv2.rectangle(frame, (startX, startY), (endX, endY),
					COLORS[idx], 2)
				y = startY - 15 if startY - 15 > 15 else startY + 15
				cv2.putText(frame, label, (startX, y),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)

				# show the output image
				cv2.imwrite( "frame.jpg", frame );
				highest_confidence = confidence

# send to pushbullet
if highest_confidence > 0:
	with open("frame.jpg", "rb") as pic:
		file_data = pb.upload_file(pic, "Person Detected")
		push = pb.push_file(**file_data)
cam.release()