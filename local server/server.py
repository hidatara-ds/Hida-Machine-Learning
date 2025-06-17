# vim: set fileencoding=utf-8 :
import os
import cv2
import numpy as np
import face_recognition
from flask import Flask, request, jsonify

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Variabel global untuk menyimpan data wajah yang dikenal
known_face_encodings =
known_face_names =

def load_known_faces():
    """
    Memuat gambar wajah dari folder 'known_faces', menghasilkan encoding,
    dan menyimpannya dalam variabel global.
    """
    print("Memuat wajah yang dikenal...")
    for filename in os.listdir('known_faces'):
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            # Ekstrak nama dari nama file (misal: Budi.jpg -> Budi)
            name = os.path.splitext(filename)
            
            # Muat file gambar
            image_path = os.path.join('known_faces', filename)
            image = face_recognition.load_image_file(image_path)
            
            # Dapatkan encoding wajah. Asumsikan hanya ada satu wajah per gambar.
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_face_encodings.append(encodings)
                known_face_names.append(name)
                print("Berhasil memuat wajah untuk: {}".format(name))
            else:
                print("Peringatan: Tidak ada wajah yang ditemukan di {}".format(filename))

@app.route('/recognize', methods=)
def recognize():
    """
    Endpoint API untuk menerima gambar dan melakukan pengenalan wajah.
    """
    # Periksa apakah ada data gambar dalam permintaan
    if not request.data:
        return jsonify({'error': 'Tidak ada data gambar'}), 400

    # Konversi data biner mentah menjadi array numpy
    nparr = np.fromstring(request.data, np.uint8)
    # Dekode array numpy menjadi gambar OpenCV
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({'error': 'Gagal mendekode gambar'}), 400

    # Temukan semua lokasi wajah dan encoding wajah dalam gambar yang diunggah
    # Menggunakan model 'hog' yang lebih cepat dan ramah CPU
    face_locations = face_recognition.face_locations(img, model="hog")
    unknown_encodings = face_recognition.face_encodings(img, face_locations)

    # Inisialisasi hasil
    # Untuk kesederhanaan, kita hanya akan mengembalikan orang pertama yang dikenali
    result_name = "Unknown"
    result_confidence = 0.0

    if unknown_encodings:
        # Ambil encoding wajah pertama yang ditemukan
        unknown_encoding = unknown_encodings
        
        # Hitung jarak antara wajah yang tidak dikenal dengan semua wajah yang dikenal
        face_distances = face_recognition.face_distance(known_face_encodings, unknown_encoding)
        
        if len(face_distances) > 0:
            # Temukan indeks dengan jarak terkecil (kecocokan terbaik)
            best_match_index = np.argmin(face_distances)
            min_distance = face_distances[best_match_index]
            
            # Terapkan ambang batas (tolerance) untuk menentukan apakah ini benar-benar cocok
            # Nilai default adalah 0.6. Jarak yang lebih kecil berarti kecocokan yang lebih baik.
            if min_distance <= 0.6:
                result_name = known_face_names[best_match_index]
                # Konversi jarak menjadi skor kepercayaan (0-100)
                # (1.0 - jarak) * 100
                result_confidence = (1.0 - min_distance) * 100
                print("Wajah dikenali: {} dengan jarak: {:.2f} (kepercayaan: {:.2f}%)".format(result_name, min_distance, result_confidence))

    # Buat respons JSON
    response_data = {
        'name': result_name,
        'confidence': round(result_confidence, 2)
    }
    
    return jsonify(response_data)

if __name__ == '__main__':
    # Muat wajah yang dikenal saat server dimulai
    load_known_faces()
    
    # Jalankan server Flask
    # Menggunakan host='0.0.0.0' agar server dapat diakses dari perangkat lain di jaringan lokal
    app.run(host='0.0.0.0', port=5000, debug=True)