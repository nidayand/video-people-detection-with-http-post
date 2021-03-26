# nidayand/video-people-detection-with-http-post
Based on nidayand/video-opencv-pushbullet but with more intelligence to remove incorrect reporting + removing Pushbullet as a requirement.
The final result of an analysis will be pushed via an HTTP POST including the image result.

OpenCV is compiled to be able to run on a Synology NAS.

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

      # Confidence level of assessed frames
      - CONFIDENCE=0.5

      # Good enough confidence level. If this level or above don't continue with the video analysis
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
- Container is searching for a person in the video frame by frame (every [FRAME env.] frame)
- If a person is spotted with a confidence above [CONFIDENCE env.] an URL-post will happen to [URLPATH env.]
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