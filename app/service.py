import requests
import json
import time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from scan import Detect

# add check for max size

uid = "opencv"
pwd = "passw0rd"
last_id = 0
url_login = "http://192.168.2.244:5000/webapi/auth.cgi?api=SYNO.API.Auth&method=Login&version=2&account={}&passwd={}&session=SurveillanceStation".format(uid,pwd)
url_check = "http://192.168.2.244:5000/webapi/entry.cgi?version=6&api=%22SYNO.SurveillanceStation.Recording%22&toTime=0&offset=0&limit=1&fromTime=0&method=%22List%22&_sid={}"

dparams = {"api": "o.8CVJHMxyRr6zyR753AGIDENm8H3wMjyn", "frames": 5, "conf": 0.2}

# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    # GET
    def do_GET(self):
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
                obj = Detect(dparams.api, dparams.conf, dparams.frames)

                # run the analysis of the file
                obj.run("/movies/"+path)

                # save id
                last_id = j["data"]["recordings"][0]["id"]
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
    print('starting server...')
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
    print('running server...')
    httpd.serve_forever()

if __name__ == "__main__":

    #login to get session
    if login():
        run()
    else:
        print("stopping service")
