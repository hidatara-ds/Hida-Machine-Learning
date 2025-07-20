from naoqi import ALProxy
import time

PEPPER_IP = "192.168.1.100"  # Ganti dengan IP Pepper kamu
PORT = 9559

face_detection = ALProxy("ALFaceDetection", PEPPER_IP, PORT)
face_recognition = ALProxy("ALFaceRecognition", PEPPER_IP, PORT)
tts = ALProxy("ALTextToSpeech", PEPPER_IP, PORT)
asr = ALProxy("ALSpeechRecognition", PEPPER_IP, PORT)

# Kata kunci untuk jawaban
vocabulary = ["yes", "no"]

def ask_yes_no(question):
    tts.say(question)
    asr.pause(True)
    asr.setVocabulary(vocabulary, False)
    asr.pause(False)
    print("Menunggu jawaban (yes/no)...")
    start = time.time()
    while time.time() - start < 5:  # Tunggu max 5 detik
        data = asr.getData()
        if data and 'word' in data:
            word = data['word']
            print("Jawaban:", word)
            return word
        time.sleep(0.5)
    return None

def main():
    face_detection.subscribe("Test_Face", 500, 0.0)
    print("Mendeteksi wajah...")

    try:
        for i in range(40):  # 20 detik
            data = face_detection.getFaces()
            if data and len(data) > 1:
                for face in data[1]:
                    extra_info = face[1]
                    if len(extra_info) > 2:
                        recognized_name = extra_info[2]
                        confidence = extra_info[1]
                        if recognized_name != "":
                            print("Wajah sudah terdaftar:", recognized_name, "Akurasi:", confidence)
                            tts.say("Hello, " + recognized_name)
                        else:
                            print("Wajah belum terdaftar.")
                            tts.say("I detect a new face. Do you want to register this face? Please answer yes or no.")
                            answer = ask_yes_no("Do you want to register this face? Please answer yes or no.")
                            if answer == "yes":
                                tts.say("Please say your name.")
                                # Here you can add code to input the name via voice or manually
                                name = "user"  # Replace with name input
                                face_recognition.learnFace(name)
                                tts.say("Face has been registered as " + name)
                            else:
                                tts.say("Okay, the face will not be registered.")
            time.sleep(0.5)
    finally:
        face_detection.unsubscribe("Test_Face")
        print("Selesai.")

if __name__ == "__main__":
    main()
