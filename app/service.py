import requests
import json
from urllib.parse import urlparse
from flask import Flask, request, render_template
from scan import Detect
import os, logging, sys
import tempfile


# set the parameters needed for the analysis
dparams = {
    "urlpath": os.getenv("URLPATH"),
    "frames": int(os.getenv("FRAMES", "5")),
    "conf": float(os.getenv("CONFIDENCE", "0.2")),
    "good_enough_conf": float(os.getenv("GOOD_ENOUGH_CONFIDENCE", "0.8")),
    "width_person": int(os.getenv("WIDTH_PERSON", "0")),
    "height_person": int(os.getenv("HEIGHT_PERSON", "0")),
    "width": int(os.getenv("WIDTH", "640")),
    "height": int(os.getenv("HEIGHT", "480")),
    "ratio": int(os.getenv("WIDTH_HEIGHT_RATIO_COMPARE_DIFF", "0")),
}

# set image correcting
scewed = (dparams["width"], dparams["height"])

app = Flask(__name__)
staticVideoPath = "/tmp/video.mp4"

uploadDirectory = '/upload-dir'

@app.route("/lookforperson", methods=["POST"])
def lookforperson():
    app.logger.info("Posted file: %s", request.files["video"])
    file = request.files["video"]

    tmp_filename = (
        tempfile._get_default_tempdir() + "/" + next(tempfile._get_candidate_names())
    )

    # Save to path
    file.save(tmp_filename)
    return check_video(tmp_filename)


# to be used by the action rule to initate the object detection
def check_video(video):
    app.logger.info("A new video to analyze!")

    # instantiate the detection object
    obj = Detect(dparams)

    try:
        # run the analysis of the file
        res = obj.run(video, scewed)
    finally:
        # delete the file
        os.remove(video)

    # save id
    return json.dumps(res)


def run():
    # start web server
    app.run(host="0.0.0.0", port=8080, debug=True)

    app.logger.debug("Started server successfully")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
