# main.py

from naoqi import qi, ALBroker, ALProxy
import face_recognition
import cv2
import time
import os
import sys
import numpy as np
import pickle
import argparse
import vision_definitions
import traceback
from PIL import Image

# ======================
# CONFIG
# ======================
DEFAULT_IP = "xxx.xxx.xxx.xxx"
DEFAULT_PORT = 9559


# ======================
# FACE RECOGNITION MAIN FUNCTION
# ======================
def idPersons(session, ip=DEFAULT_IP, port=DEFAULT_PORT):
    # Connect to Pepper's services
    videoService = session.service('ALVideoDevice')
    tts = session.service('ALTextToSpeech')

    SID = "pepper_face_recognition"
    resolution = vision_definitions.kQVGA  # 320x240
    colorSpace = vision_definitions.kRGBColorSpace
    nameId = videoService.subscribe(SID, resolution, colorSpace, 10)

    # Load face encodings and names
    with open('encodings_names', 'rb') as fp:
        known_face_names = pickle.load(fp)
    with open('encodings', 'rb') as fp:
        known_face_encodings = pickle.load(fp)

    # Setup image and control variables
    width, height = 320, 240
    scale = 0.5
    revscale = 1 / scale
    process_this_frame = 0
    blank_image = np.zeros((width, height, 3), np.uint8)
    greeted = []

    try:
        while True:
            try:
                result = videoService.getImageRemote(nameId)
                image = None

                if result is None or result[6] is None:
                    print("No image data.")
                    continue

                image_string = str(result[6])
                im = Image.frombytes("RGB", (width, height), image_string)
                image = np.asarray(im)

            except Exception as e:
                print("Image capture error:", e)
                traceback.print_exc()
                continue

            if image is not None:
                if process_this_frame == 0:
                    small_frame = cv2.resize(image, (0, 0), fx=scale, fy=scale)
                    face_locations = face_recognition.face_locations(small_frame)
                    face_encodings = face_recognition.face_encodings(small_frame, face_locations)
                    face_names = []

                    for face_encoding in face_encodings:
                        distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        name = "Unknown"
                        blank_image[:, :] = (0, 0, 255)

                        if len(distances) > 0:
                            min_distance = np.min(distances)
                            min_index = np.argmin(distances)

                            if min_distance < 0.53:
                                name = known_face_names[min_index]
                                blank_image[:, :] = (0, 255, 0)

                                if name not in greeted:
                                    tts.say("Hi " + name + "! Nice to see you.")
                                    greeted.append(name)

                        face_names.append(name)

                process_this_frame = (process_this_frame + 1) % 2

                # Draw results
                bgr_image = image[:, :, ::-1]
                for (top, right, bottom, left), name in zip(face_locations, face_names):
                    top = int(top * revscale)
                    right = int(right * revscale)
                    bottom = int(bottom * revscale)
                    left = int(left * revscale)

                    color = (0, 255, 0) if name != "Unknown" else (255, 0, 0)
                    text_color = (0, 0, 0) if name != "Unknown" else (255, 255, 255)

                    cv2.rectangle(bgr_image, (left, top), (right, bottom), color, 2)
                    cv2.rectangle(bgr_image, (left, bottom + 70), (right, bottom), color, cv2.FILLED)
                    cv2.putText(bgr_image, name, (left + 6, bottom + 29), cv2.FONT_HERSHEY_DUPLEX, 1.0, text_color, 1)

                # Display
                frame_resized = cv2.resize(bgr_image, (0, 0), fx=0.75, fy=0.75)
                cv2.imshow('Video', frame_resized)
                cv2.imshow('Access', blank_image)

                # Keyboard controls
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    with open('encodings_names', 'rb') as fp:
                        known_face_names = pickle.load(fp)
                    with open('encodings', 'rb') as fp:
                        known_face_encodings = pickle.load(fp)
                    print('Reloaded encodings.')

    except Exception as e:
        print("Error in main loop:", e)
        traceback.print_exc()
    finally:
        cv2.destroyAllWindows()


# ======================
# ENTRY POINT
# ======================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default=DEFAULT_IP, help="Robot IP address. Use '127.0.0.1' for local.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Naoqi port number. Default is 9559.")
    args = parser.parse_args()

    session = qi.Session()
    try:
        session.connect(f"tcp://{args.ip}:{args.port}")
    except RuntimeError:
        print(f"Can't connect to Naoqi at ip \"{args.ip}\" on port {args.port}.\nCheck script arguments. Use -h for help.")
        sys.exit(1)

    idPersons(session, args.ip, args.port)
