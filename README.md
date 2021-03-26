# nidayand/video-people-detection-with-http-post
Based on nidayand/video-opencv-pushbullet but with more intelligence to remove incorrect reporting + removing Pushbullet as a requirement.
The final result of an analysis will be pushed via an HTTP POST including the image result.

OpenCV is compiled to be able to run on a Synology NAS.

## Build
docker-compose build

## Parameters
See [docker-compose.yml](https://github.com/nidayand/video-people-detection-with-http-post/blob/main/docker-compose.yml) example

## Behaviour
- Container includes a webserver that listens to a POST request on "/lookforperson" path
- The POST request must include a video file to be analysed. Parameter "video"
- Container is searching for a person in the video frame by frame (every [FRAME env.] frame)
- If a person is spotted with a confidence above [CONFIDENCE env.] an URL-post will happen to [URLPATH env.]
- The result will be returned in a JSON string

```javascript
{"success": true, "confidence": "0.7131952", "width": 14, "height": 31, "ratio_diff": 10, "comment": "Person was found"}
```

### Incoming PATH
POST request: http://127.0.0.1:8094/lookforperson?video={mp4 to be analyzed}

Path must be file system accessible path for the docker container.

## Test
```bash
curl -v -F video=@Garage_07-13-12.mp4 http://127.0.0.1:8094/lookforperson
```

Example Node-RED as backend to show the result
```javascript
[{"id":"64002901.0fe618","type":"http in","z":"5c98d892.1f31c8","name":"","url":"/videonotify","method":"post","upload":true,"swaggerDoc":"","x":460,"y":180,"wires":[["20177ddc.2a7f92","6328d5fe.6d717c","f4fd9714.24ebb8"]]},{"id":"20177ddc.2a7f92","type":"debug","z":"5c98d892.1f31c8","name":"","active":true,"tosidebar":true,"console":false,"tostatus":false,"complete":"true","targetType":"full","x":870,"y":180,"wires":[]},{"id":"6328d5fe.6d717c","type":"http response","z":"5c98d892.1f31c8","name":"","statusCode":"200","headers":{},"x":670,"y":260,"wires":[]},{"id":"f4fd9714.24ebb8","type":"image","z":"5c98d892.1f31c8","name":"","width":"640","data":"req.files[0].buffer","dataType":"msg","thumbnail":false,"active":true,"pass":false,"outputs":0,"x":900,"y":260,"wires":[]}]
```