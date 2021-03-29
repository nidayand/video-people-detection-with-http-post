# nidayand/video-people-detection-with-http-post
The container includes a webserver that is listening after an incoming HTTP POST message to `/lookforperson` path. The incoming message must include a video to be analyzed on a parameter named `video`.
Based on the environment settings it will look for a person in the frames of the video and if found it will do an HTTP POST to a server address of choice and include the detected frame, with the highest confidence level, and the details of the detection.

OpenCV is compiled to be able to run on a Synology NAS.

![Sample](https://i.imgur.com/YCfSBOR.jpg)

### Input:
HTTP post to `/lookforperson`
#### Parameters:
- `video`: (POST parameter) File to be analyzed

### Action
HTTP post to the address specified 
- `file`: JPG file object attached with the post including the detection

### Output
The HTTP POST response with be a JSON document and if successful (found a person) it will have the format as per below. `params` are the incoming variables used in the analysis.
```json
{
   "success":true,
   "confidence":"0.71319485",
   "width":14,
   "height":31,
   "ratio_diff":10,
   "comment":"Person was found",
   "params":"{\"urlpath\": \"http://192.168.2.244:1881/reportpersoninvideo\", \"frames\": 5, \"conf\": 0.2, \"good_enough_conf\": 0.7, \"width_person\": 40, \"height_person\": 80, \"width\": 640, \"height\": 480, \"ratio\": 20}"
}
```

## How I use it
I use the container to get rid of CCTV notification noise - i.e. I'm alerted only if a person is detected around my house
1. Using MotionEye OS I have 6 video streams the is triggering recordings based on changes in the number of pixels in a frame
2. If a motion is detected MotionEye will run a command when the file has been saved
```bash
curl -F video=@%f http://192.168.2.244:8094/lookforperson
```
![MotionEye](https://i.imgur.com/nE9e9c9.png)

3. `curl` does a post of the mp4 file to the docker container
4. The container will post the result to a Node-RED instance that listens to a HTTP POST with a video and it will send the image further to my Discord server

![Node-RED](https://i.imgur.com/PuOfo95.png)

## docker-compose.yml
```yaml
version: "2"
services:
  people_recognition:
    container_name: opencv_findperson
    build:
      context: .
      dockerfile: Dockerfile
    image: "nidayand/video-people-detection-with-http-post"
    ports:
      - "8094:8080"
    environment: 
      # URL to post image result to. Path will be appended with a field called "file" with type image/jpg
      - URLPATH=http://192.168.2.104:1880/videonotify

      # Required minimun level of confidence when detected a person on the analysis of a frame. Default 0.2
      - CONFIDENCE=0.5

      # Good enough confidence level. Skip additional frame analysis when this level has been reached. Default 0.8
      - GOOD_ENOUGH_CONFIDENCE=0.7

      # Every x frame will be checked for a person
      - FRAMES=5

      # Resizing frame for analysis to improve performance. Default values 640/480
      - WIDTH=640
      - HEIGHT=480

      # MAX % of image that can be a person
      # Set to 0 to disable or remove entry
      - WIDTH_PERSON=30
      - HEIGHT_PERSON=60

      # Validate that height/width of a person is not above difference compared to max HEIGHT_PERSON/WIDTH_PERSON
      # Avoids strange dimensions e.g. 50x3 when more likely 50x25
      # Set to 0 to disable or remove entry
      - WIDTH_HEIGHT_RATIO_COMPARE_DIFF=20  
```



## Build
```bash
docker-compose build
```

## Behaviour
- Container includes a webserver that listens to a POST request on `"/lookforperson"` path
- The POST request must include a video file to be analysed. Parameter `"video"`
- Container is searching for a person in the video frame by frame (every `[FRAME env.]` frame)
- If a person is spotted with a confidence above `[CONFIDENCE env.]` an URL-post will happen to `[URLPATH env.]``
- If `[GOOD_ENOUGH_CONFIDENCE env.]` is set the frame scanning will stop when a value is found above otherwise it will assess the entire video
- If the width or height is larger that `[WIDTH_PERSON]` or `[HEIGHT_PERSON]` the frame will be skipped
- If the person detected will have a larger ratio that `[WIDTH_PERSON]/[HEIGHT_PERSON]` the frame will be skipped
- The result will be returned in a JSON string

```javascript
{"success": true, "confidence": "0.7131952", "width": 14, "height": 31, "ratio_diff": 10, "comment": "Person was found"}
```

## Test
```bash
curl -v -F video=@Garage_07-13-12.mp4 http://127.0.0.1:8094/lookforperson
```

Example Node-RED as backend to show the result
```javascript
[{"id":"64002901.0fe618","type":"http in","z":"5c98d892.1f31c8","name":"","url":"/videonotify","method":"post","upload":true,"swaggerDoc":"","x":460,"y":180,"wires":[["20177ddc.2a7f92","6328d5fe.6d717c","f4fd9714.24ebb8"]]},{"id":"20177ddc.2a7f92","type":"debug","z":"5c98d892.1f31c8","name":"","active":true,"tosidebar":true,"console":false,"tostatus":false,"complete":"true","targetType":"full","x":870,"y":180,"wires":[]},{"id":"6328d5fe.6d717c","type":"http response","z":"5c98d892.1f31c8","name":"","statusCode":"200","headers":{},"x":670,"y":260,"wires":[]},{"id":"f4fd9714.24ebb8","type":"image","z":"5c98d892.1f31c8","name":"","width":"640","data":"req.files[0].buffer","dataType":"msg","thumbnail":false,"active":true,"pass":false,"outputs":0,"x":900,"y":260,"wires":[]}]
```