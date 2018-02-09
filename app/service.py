import requests
import json
import time, threading
import web

# add check for max size

uid = "opencv"
pwd = "passw0rd"
sid = ""
check_period_seconds = 10
url_login = "http://192.168.2.244:5000/webapi/auth.cgi?api=SYNO.API.Auth&method=Login&version=2&account={}&passwd={}&session=SurveillanceStation".format(uid,pwd)
url_check = "http://192.168.2.244:5000/webapi/entry.cgi?version=6&api=%22SYNO.SurveillanceStation.Recording%22&toTime=0&offset=0&limit=1&fromTime=0&method=%22List%22&_sid={}"

urls = (
  '/', 'index'
)

# extend ctx for the web server to access the global variables
def add_global_hook():
    global url_check
    g = web.storage({"url_check": url_check, "last_id":0})
    def _wrapper(handler):
        web.ctx.globals = g
        return handler()
    return _wrapper

# to be used by the action rule to initate the object detection
class index:
    def GET(self):
        global check_period_seconds, last_id, app

        # call the list url
        myResponse = requests.get(web.ctx.globals.url_check, verify=True)
        if myResponse.ok:
            #convert to object
            j = json.loads(myResponse.content)
            if j["success"]:
                if web.ctx.globals.last_id != 0 and web.ctx.globals.last_id != j["data"]["recordings"][0]["id"]:
                    # new entry
                    path = j["data"]["recordings"][0]["cameraName"]+"/"+j["data"]["recordings"][0]["filePath"]

                    # save id
                    web.ctx.globals.last_id = j["data"]["recordings"][0]["id"]
                    return json.dumps({"success:": True, "update": True, "value": path,"id" :web.ctx.globals.last_id})
                else:
                    # save id
                    web.ctx.globals.last_id = j["data"]["recordings"][0]["id"]
                    return json.dumps({"success:": True, "update": False, "value": "no update", "id" :web.ctx.globals.last_id})


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

if __name__ == "__main__":

    #login to get session
    if login():
        app = web.application(urls, globals())
        app.add_processor(add_global_hook())
        app.run()
    else:
        print("stopping service")
