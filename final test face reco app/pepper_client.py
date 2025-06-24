# pepper_client.py
import qi
import requests
import os
import base64
import argparse
import time

# --- KONFIGURASI ---
# Ganti dengan alamat IP eksternal VM Google Compute Engine kamu
GCE_EXTERNAL_IP = "34.101.50.100" 
BASE_URL = f"http://{GCE_EXTERNAL_IP}:8000"

class PepperFaceRecognizer:
    def __init__(self, app):
        """
        Inisialisasi koneksi ke Pepper.
        """
        super(PepperFaceRecognizer, self).__init__()
        app.start()
        session = app.session
        
        # Dapatkan service yang dibutuhkan
        self.memory = session.service("ALMemory")
        self.tts = session.service("ALTextToSpeech")
        self.photo_capture = session.service("ALPhotoCapture")
        
        print("Koneksi ke Pepper berhasil.")

    def take_and_recognize_picture(self):
        """
        Mengambil gambar, mengirimnya ke server, dan mengucapkan hasilnya.
        """
        self.tts.say("Oke, saya akan coba kenali wajah di depan saya. Tolong lihat ke kamera ya.")
        time.sleep(1)

        # Konfigurasi pengambilan gambar
        picture_path = "/home/nao/recordings/cameras/"
        file_name = "face_capture.jpg"
        full_path = os.path.join(picture_path, file_name)
        
        # Set resolusi kamera (2 = 640x480)
        self.photo_capture.setResolution(2)
        # Ambil gambar
        self.photo_capture.takePicture(picture_path, file_name)
        
        print(f"Gambar berhasil diambil dan disimpan di: {full_path}")
        self.tts.say("Oke, foto sudah diambil. Sekarang saya proses dulu ya.")

        # Kirim gambar ke server untuk dikenali
        self.send_for_recognition(full_path)

    def send_for_recognition(self, image_path):
        """
        Mengirim file gambar ke server GCE.
        """
        print(f"Mengirim {image_path} ke server di {BASE_URL}/recognize")
        url = f"{BASE_URL}/recognize"
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
                response = requests.post(url, files=files, timeout=20) # Tambah timeout
                response.raise_for_status()
                
                data = response.json()
                print("Respons dari server:", data)

                # Pepper mengucapkan hasilnya
                if data.get("status") == "recognized":
                    nama = data.get("name")
                    confidence = data.get("confidence")
                    self.tts.say(f"Halo {nama}, selamat datang kembali. Tingkat kepercayaan saya {confidence}.")
                elif data.get("status") == "unrecognized":
                    self.tts.say("Maaf, wajah anda tidak saya kenali. Silakan mendaftar.")
                else:
                    self.tts.say("Maaf, terjadi kesalahan di server.")

        except requests.exceptions.RequestException as e:
            print(f"Error saat mengirim request ke server: {e}")
            self.tts.say("Aduh, sepertinya saya tidak bisa terhubung ke server.")


if __name__ == "__main__":
    # Konfigurasi untuk koneksi ke Pepper
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="192.168.1.100",
                        help="Alamat IP Robot Pepper.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Nomor port Naoqi.")
    args = parser.parse_args()

    try:
        # Inisialisasi koneksi Qi
        connection_url = f"tcp://{args.ip}:{args.port}"
        app = qi.Application(["PepperFaceRecognizer", "--qi-url=" + connection_url])
    except RuntimeError:
        print(f"Tidak bisa terhubung ke Naoqi di {args.ip}:{args.port}. Pastikan sudah benar.")
        exit(1)

    # Jalankan aplikasi
    recognizer = PepperFaceRecognizer(app)
    recognizer.take_and_recognize_picture()

    print("Selesai.") 