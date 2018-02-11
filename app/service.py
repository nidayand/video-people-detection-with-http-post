import requests
import json
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from scan import Detect
import os

# Envi
# MAX_SIZE (20) = Maximum filesize of the file to be analyzed
# PUSHBULLET = API key
# FRAMES  (5)= check every x frames
# CONFIDENCE (0.2) = level of assurance
# USERNAME = synology username to access the web api
# PASSWORD
# WEBAPIPATH (http://127.0.0.1:5000/webapi) = path to web api
# WIDTH (640) = Correction of image in pixels
# HEIGHT (480) = Correction of image in pixels

last_id = 0

# set image correcting
scewed = (int(os.getenv("WIDTH","640")), int(os.getenv("HEIGHT","480")))

# accessing the json apis of surveillance station
url_login = os.getenv("WEBAPIPATH","http://192.168.2.2:5000/webapi")+"/auth.cgi?api=SYNO.API.Auth&method=Login&version=2&account={}&passwd={}&session=SurveillanceStation".format(os.getenv("USERNAME"),os.getenv("PASSWORD"))
url_check = os.getenv("WEBAPIPATH","http://192.168.2.2:5000/webapi")+"/entry.cgi?version=6&api=%22SYNO.SurveillanceStation.Recording%22&toTime=0&offset=0&limit=1&fromTime=0&method=%22List%22&_sid={}"

# set the parameters needed for the analysis
dparams = {"api": os.getenv("PUSHBULLET"), "frames": int(os.getenv('FRAMES',"5")), "conf": float(os.getenv('CONFIDENCE',"0.2"))}

# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    # GET
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/poll':
            print(parsed_path)
            self.send_response(200)

            # Send message back to client
            message = check_list()
            response = bytes(str(message), "utf8")

            # Send headers
            self.send_header('Content-type','text/json')
            self.send_header("Content-Length", len(response))
            self.end_headers()

            # Write content as utf-8 data
            self.wfile.write(response)
        else:
            self.send_error(500,"incorrect path")

# to be used by the action rule to initate the object detection
def check_list():
    global url_check, check_period_seconds, last_id, app

    # call the list url
    myResponse = requests.get(url_check, verify=True)
    if myResponse.ok:
        #convert to object
        j = json.loads(myResponse.content)
        if j["success"]:
            if last_id != 0 and last_id != j["data"]["recordings"][0]["id"]:
                # new entry
                path = j["data"]["recordings"][0]["cameraName"]+"/"+j["data"]["recordings"][0]["filePath"]

                # instantiate the detection object
                obj = Detect(dparams["api"], dparams["conf"], dparams["frames"])

                # as there is a delay in processing, update the last id
                last_id = j["data"]["recordings"][0]["id"]

                # run the analysis of the file
                obj.run("/movies/"+path, scewed)

                # save id
                return json.dumps({"success:": True, "update": True, "value": path,"id" :last_id})
            else:
                # save id
                last_id = j["data"]["recordings"][0]["id"]
                return json.dumps({"success:": True, "update": False, "value": "no update", "id" :last_id})


        else:
            return json.dumps({"success:": False, "update": False, "value": "failed to get list data"})

    else:
        return json.dumps({"success:": False, "update": False, "value": "did not receive a response from surveillance station"})


def login():
    global url_check
    myResponse = requests.get(url_login, verify=True)
    if myResponse.ok:
        # convert to object
        j = json.loads(myResponse.content)
        if j["success"]:
            # update the list url with the sid
            url_check = url_check.format(j["data"]["sid"])

            print("successful login")
            return True
        else:
            return False
            print("Failed to authenticate")
    else:
        return False
        print("Failed to authenticate")

def run():
    # start web server
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
    print('started server')
    httpd.serve_forever()

    # initiate list variables by getting the latest id
    check_list()

if __name__ == "__main__":

    #login to get session
    if login():
        run()
    else:
        print("stopping service")
