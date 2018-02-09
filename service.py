import requests
import json
import time, threading

# add check for max size

uid = "opencv"
pwd = "passw0rd"
sid = ""
last_id = 0
check_period_seconds = 10

url_login = "http://192.168.2.244:5000/webapi/auth.cgi?api=SYNO.API.Auth&method=Login&version=2&account={}&passwd={}&session=SurveillanceStation".format(uid,pwd)

url_check = "http://192.168.2.244:5000/webapi/entry.cgi?version=6&api=%22SYNO.SurveillanceStation.Recording%22&toTime=0&offset=0&limit=1&fromTime=0&method=%22List%22&_sid={}"

# Check for new updates
def check_update():
    print(time.ctime())
    global url_check, check_period_seconds, last_id

    # call the list url
    myResponse = requests.get(url_check, verify=True)
    if myResponse.ok:
        #convert to object
        j = json.loads(myResponse.content)
        if j["success"]:
            if last_id != 0 and last_id != j["data"]["recordings"][0]["id"]:
                # new entry
                path = j["data"]["recordings"][0]["cameraName"]+"/"+j["data"]["recordings"][0]["filePath"]
                print(path)
                print(j)

            # save id
            last_id = j["data"]["recordings"][0]["id"]

            # call method again
            threading.Timer(check_period_seconds, check_update).start()
        else:
            print("Failed to get list data")


def login():
    print(url_login)
    myResponse = requests.get(url_login, verify=True)
    if myResponse.ok:
        # convert to object
        j = json.loads(myResponse.content)
        if j["success"]:
            # update the list url with the sid
            global url_check
            url_check = url_check.format(j["data"]["sid"])

            print("successful login")

            # initiate checking for updates
            check_update()
        else:
            print("Failed to authenticate")
    else:
        print("Failed to authenticate")

login()
