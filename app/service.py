import requests
import json
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from scan import Detect
import os

"""
MAX_SIZE (20) = Maximum filesize of the file to be analyzed
PUSHBULLET = API key
FRAMES  (5)= check every x frames
CONFIDENCE (0.2) = level of assurance
WIDTH (640) = Correction of image in pixels
HEIGHT (480) = Correction of image in pixels
"""

# set image correcting
scewed = (int(os.getenv("WIDTH", "640")), int(os.getenv("HEIGHT", "480")))

# set the parameters needed for the analysis
dparams = {"api": os.getenv("PUSHBULLET"),
           "frames": int(os.getenv('FRAMES', "5")),
           "conf": float(os.getenv('CONFIDENCE', "0.2"))}


# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    # GET
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/findperson':
            # get video parameter
            query = urlparse(self.path).query
            query_components = dict(qc.split("=") for qc in query.split("&"))
            video = query_components["video"]

            # Send message back to client
            message = check_video(video)
            self.send_response(200)
            response = bytes(str(message), "utf8")

            # Send headers
            self.send_header('Content-type', 'text/json')
            self.send_header("Content-Length", len(response))
            self.end_headers()

            # Write content as utf-8 data
            self.wfile.write(response)
        #else:
        #    self.send_error(500, "incorrect path")


# to be used by the action rule to initate the object detection
def check_video(video):
    print("A new video to analyze!")

    # instantiate the detection object
    obj = Detect(dparams["api"],
                 dparams["conf"],
                 dparams["frames"])

    # run the analysis of the file
    obj.run("/videos/"+video, scewed)

    # save id
    return json.dumps({"success:": True,
                       "value": video })

def run():
    # start web server
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)

    print('started server')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
