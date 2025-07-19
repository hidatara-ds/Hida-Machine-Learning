import time
import sys
import os
# Note: 'requests' and 'json' are imported after the sys.path modification

class MyClass(GeneratedClass):
    def __init__(self):
        GeneratedClass.__init__(self, False)
        self.resolutionMap = {
            '160 x 120': 0, '320 x 240': 1,
            '640 x 480': 2, '1280 x 960': 3
        }
        self.cameraMap = {'Top': 0, 'Bottom': 1}
        # The original record folder is fine, as it's a known path on the robot
        self.recordFolder = "/home/nao/recordings/cameras/"
        self.tts = None # Initialize tts proxy

    def onLoad(self):
        self.bIsRunning = False
        try:
            self.photoCapture = ALProxy("ALPhotoCapture")
            self.tts = ALProxy("ALTextToSpeech") # Create proxy for speech
        except Exception as e:
            self.photoCapture = None
            self.logger.error(e)

    def onUnload(self):
        pass

    def onInput_onStart(self):
        # === START: DYNAMIC LIBRARY LOADING ===
        # This block must come first to enable the 'requests' import.
        try:
            behavior_path = self.behaviorAbsolutePath()
            lib_path = os.path.join(behavior_path, "lib")
            if lib_path not in sys.path:
                sys.path.append(lib_path)
            import requests
            import json
        except Exception as e:
            self.logger.error("Failed to import requests library: %s" % str(e))
            self.tts.say("I have a problem with my communication module.")
            self.onStopped()
            return
        # === END: DYNAMIC LIBRARY LOADING ===

        if(self.bIsRunning):
            return
        self.bIsRunning = True

        resolution = self.resolutionMap
        cameraID = self.cameraMap[self.getParameter("Camera")]
        fileName = self.getParameter("File Name") # e.g., "test"

        if self.photoCapture:
            self.photoCapture.setResolution(resolution)
            self.photoCapture.setCameraID(cameraID)
            self.photoCapture.setPictureFormat("jpg")
            
            # This saves the picture on the robot's local storage
            self.photoCapture.takePicture(self.recordFolder, fileName)
            
            # === START: API COMMUNICATION LOGIC ===
            # The image is now saved. Let's send it to the API.
            image_filename = fileName + ".jpg"
            image_path = os.path.join(self.recordFolder, image_filename)
            
            # The static IP of your GCP VM instance
            api_url = "http://<YOUR_STATIC_IP>:8000/recognize" # IMPORTANT: Replace with your actual IP

            if not os.path.exists(image_path):
                self.logger.error("Image file not found at: %s" % image_path)
                self.tts.say("I couldn't find the picture I just took.")
            else:
                try:
                    self.tts.say("Let me see who you are.")
                    with open(image_path, 'rb') as img_file:
                        files = {'image': (image_filename, img_file, 'image/jpeg')}
                        # Send the request with a timeout
                        response = requests.post(api_url, files=files, timeout=20)

                    # Process the response
                    if response.status_code == 200:
                        data = response.json()
                        identity = data.get('identity', 'someone new')
                        if identity == 'unknown':
                            self.tts.say("I don't believe we have met before.")
                        else:
                            # Replace underscores with spaces for more natural speech
                            friendly_name = identity.replace('_', ' ')
                            self.tts.say("Hello, " + friendly_name)
                    else:
                        self.logger.error("API Error: Status %d, Response: %s" % (response.status_code, response.text))
                        self.tts.say("I'm having trouble connecting to my brain.")

                except requests.exceptions.RequestException as e:
                    self.logger.error("Network request failed: %s" % str(e))
                    self.tts.say("I can't seem to reach the network right now.")
                except Exception as e:
                    self.logger.error("An unexpected error occurred during API call: %s" % str(e))
                    self.tts.say("Something went wrong while I was thinking.")
            # === END: API COMMUNICATION LOGIC ===

        self.bIsRunning = False
        self.onStopped()