# vim: set fileencoding=utf-8 :
import sys
import time
import cv2
import numpy as np
import requests
from naoqi import ALProxy
import vision_definitions

# --- Konfigurasi ---
# Ganti dengan alamat IP Robot Anda
ROBOT_IP = "192.168.1.10" 
# Ganti dengan alamat IP komputer yang menjalankan server.py
SERVER_IP = "192.168.1.5"
PORT = 9559
SERVER_URL = "http://{}:5000/recognize".format(SERVER_IP)

def main():
    """
    Fungsi utama untuk menjalankan alur pengenalan wajah.
    """
    # Inisialisasi proksi
    try:
        videoDevice = ALProxy("ALVideoDevice", ROBOT_IP, PORT)
        tts = ALProxy("ALTextToSpeech", ROBOT_IP, PORT)
    except Exception as e:
        print "Gagal membuat proksi: {}".format(e)
        sys.exit(1)

    # Berlangganan ke kamera atas robot
    # Handle ini penting untuk dilepaskan nanti
    name = "face_recognition_client"
    camera_id = 0 # Kamera Atas
    resolution = vision_definitions.kQVGA # 320x240
    color_space = vision_definitions.kBGRColorSpace # 13
    fps = 10
    
    capture_handle = None
    try:
        capture_handle = videoDevice.subscribeCamera(name, camera_id, resolution, color_space, fps)
        print "Berhasil berlangganan ke kamera dengan handle: {}".format(capture_handle)
        
        # Beri sedikit waktu agar kamera stabil
        time.sleep(1)

        print "Mengambil gambar..."
        result = videoDevice.getImageRemote(capture_handle)

        if result is None:
            print "Tidak dapat mengambil gambar."
            return

        # Dekode data gambar dari format NAOqi
        width = result
        height = result
        image_data_string = result
        
        # Konversi string bita menjadi array NumPy yang dapat digunakan oleh OpenCV
        image_numpy = np.fromstring(image_data_string, dtype=np.uint8).reshape((height, width, 3))
        
        print "Gambar berhasil diambil ({}x{})".format(width, height)
        # Simpan gambar secara lokal untuk debugging (opsional)
        # cv2.imwrite("captured_image.jpg", image_numpy)

        # Enkode gambar ke format JPEG untuk dikirim melalui jaringan
        _, img_encoded = cv2.imencode('.jpg', image_numpy)
        
        # Siapkan header untuk permintaan POST
        headers = {'content-type': 'image/jpeg'}

        print "Mengirim gambar ke server di {}".format(SERVER_URL)
        
        try:
            # Kirim permintaan POST dengan data gambar
            response = requests.post(SERVER_URL, data=img_encoded.tostring(), headers=headers, timeout=10)

            # Periksa respons dari server
            if response.status_code == 200:
                data = response.json()
                name = data.get('name', 'Unknown')
                confidence = data.get('confidence', 0)
                
                print "Respons diterima: Nama = {}, Kepercayaan = {}%".format(name, confidence)

                # Buat robot mengucapkan hasilnya
                if name!= "Unknown" and confidence > 50:
                    greeting = "Halo, {}".format(name)
                else:
                    greeting = "Maaf, saya tidak mengenali Anda."
                
                tts.say(greeting)

            else:
                print "Server mengembalikan galat: {}".format(response.status_code)
                tts.say("Ada masalah dengan server pengenalan.")

        except requests.exceptions.RequestException as e:
            print "Gagal terhubung ke server: {}".format(e)
            tts.say("Saya tidak bisa terhubung ke server.")

    finally:
        # Pastikan kita selalu berhenti berlangganan dari kamera untuk melepaskan sumber daya
        if capture_handle:
            print "Berhenti berlangganan dari kamera..."
            videoDevice.unsubscribe(capture_handle)

if __name__ == "__main__":
    main()