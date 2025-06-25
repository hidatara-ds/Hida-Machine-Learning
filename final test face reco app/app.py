# app.py
import os
import uuid
import base64
from flask import Flask, request, jsonify
from deepface import DeepFace
import pandas as pd
from gcs_handler import synchronize_gcs_to_local, upload_face_to_gcs, LOCAL_DB_PATH

# Tidak perlu set credential di sini, sudah diatur di gcs_handler.py

app = Flask(__name__)

# --- Konfigurasi ---
# Pilih model dan metrik jarak yang akan digunakan
MODEL_NAME = "VGG-Face"
DISTANCE_METRIC = "cosine"
# Atur ambang batas jarak berdasarkan Tabel 2
DISTANCE_THRESHOLD = 0.6
# Direktori sementara untuk menyimpan file yang diunggah
UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Pesan respons standar
UNRECOGNIZED_MESSAGE = "wajah anda tidak saya kenali silahkan daftarkan wajah anda"

@app.route('/recognize', methods=['POST'])
def recognize_face():
    """
    Endpoint untuk mengenali wajah dari gambar yang diunggah.
    """
    # Lakukan sinkronisasi cerdas di setiap request untuk memastikan database selalu terbaru
    synchronize_gcs_to_local()

    # Periksa apakah ada file gambar dalam permintaan
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada file gambar dalam permintaan"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Nama file kosong"}), 400

    if file:
        # Simpan file sementara
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        temp_image_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_image_path)

        try:
            # Gunakan DeepFace.find untuk mencari wajah di database lokal
            # enforce_detection=False agar tidak error jika tidak ada wajah
            dfs = DeepFace.find(
                img_path=temp_image_path,
                db_path=LOCAL_DB_PATH,
                model_name=MODEL_NAME,
                distance_metric=DISTANCE_METRIC,
                enforce_detection=False
            )

            # DeepFace.find mengembalikan list of dataframes. Kita proses dataframe pertama.
            if not dfs or dfs[0].empty:
                print("Wajah tidak ditemukan di database atau tidak ada kecocokan.")
                return jsonify({"status": "unrecognized", "message": UNRECOGNIZED_MESSAGE})

            # Ambil dataframe hasil dari list
            result_df = dfs[0]
            
            # Ambil baris pertama (kecocokan terbaik)
            best_match = result_df.iloc[0]
            
            # Cari nama kolom jarak secara dinamis.
            distance_column_name = [col for col in result_df.columns if DISTANCE_METRIC in col]
            
            # Jika tidak ketemu, coba gunakan nama kolom 'distance' sebagai fallback
            if not distance_column_name:
                if 'distance' in result_df.columns:
                    distance_column_name = ['distance']
                else:
                    raise KeyError(f"Tidak dapat menemukan kolom jarak. Kolom yang tersedia: {list(result_df.columns)}")

            # Ambil jarak dari kolom yang ditemukan
            distance = best_match[distance_column_name[0]]
            
            # Periksa apakah jarak di bawah ambang batas
            if distance <= DISTANCE_THRESHOLD:
                # Ekstrak nama dari path identitas
                identity_path = best_match['identity']
                
                # Coba ekstrak nama dari struktur folder bersarang (gcs_database/NAMA/file.jpg)
                person_name = os.path.basename(os.path.dirname(identity_path))
                
                # Jika hasilnya adalah nama folder database itu sendiri, berarti strukturnya datar (gcs_database/NAMA.jpg)
                # Maka, kita ambil nama dari nama filenya.
                if person_name == LOCAL_DB_PATH:
                    person_name = os.path.splitext(os.path.basename(identity_path))[0]

                # Hitung skor kepercayaan sebagai kebalikan dari jarak
                confidence_score = (1 - distance) * 100

                print(f"Wajah dikenali sebagai: {person_name} dengan jarak: {distance} (kepercayaan: {confidence_score:.2f}%)")
                return jsonify({
                    "status": "recognized", 
                    "name": person_name, 
                    "distance": float(distance),
                    "confidence": f"{confidence_score:.2f}%"
                })
            else:
                print(f"Kecocokan ditemukan tetapi jarak ({distance}) di atas ambang batas ({DISTANCE_THRESHOLD}).")
                return jsonify({"status": "unrecognized", "message": UNRECOGNIZED_MESSAGE})

        except Exception as e:
            print(f"Error selama pemrosesan DeepFace: {e}")
            # Jika error karena tidak ada wajah terdeteksi di gambar input
            if "Face could not be detected" in str(e):
                 return jsonify({"status": "error", "message": "Tidak ada wajah yang terdeteksi di gambar."})
            return jsonify({"status": "error", "message": f"Terjadi kesalahan internal: {str(e)}"})
        finally:
            # Hapus file sementara setelah diproses
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
    
    return jsonify({"status": "error", "message": "Terjadi kesalahan yang tidak diketahui."}), 500


@app.route('/register', methods=['POST'])
def register_face():
    """
    Endpoint untuk mendaftarkan wajah baru.
    Menerima JSON dengan 'name' dan 'image' (base64 encoded).
    """
    data = request.get_json()
    if not data or 'name' not in data or 'image' not in data:
        return jsonify({"status": "error", "message": "Permintaan tidak valid. 'name' dan 'image' diperlukan."}), 400

    person_name = data['name']
    image_data = data['image']

    try:
        # Decode gambar base64 dan simpan sementara
        image_bytes = base64.b64decode(image_data)
        filename = f"{person_name}_{uuid.uuid4()}.jpg"
        temp_image_path = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(temp_image_path, 'wb') as f:
            f.write(image_bytes)

        # Unggah gambar ke GCS
        success = upload_face_to_gcs(temp_image_path, person_name)

        if success:
            # Setelah pendaftaran, sinkronkan kembali GCS ke lokal agar wajah baru tersedia
            print("Memperbarui database lokal setelah pendaftaran baru...")
            synchronize_gcs_to_local()
            return jsonify({"status": "success", "message": f"Wajah untuk {person_name} berhasil didaftarkan."})
        else:
            return jsonify({"status": "error", "message": "Gagal mengunggah gambar ke GCS."}), 500

    except Exception as e:
        print(f"Error selama pendaftaran: {e}")
        return jsonify({"status": "error", "message": f"Terjadi kesalahan internal: {str(e)}"}), 500
    finally:
        # Hapus file sementara
        if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
            os.remove(temp_image_path)


if __name__ == '__main__':
    # Saat startup, cukup pastikan folder database lokal ada.
    # Sinkronisasi penuh akan dijalankan oleh request pertama.
    if not os.path.exists(LOCAL_DB_PATH):
        os.makedirs(LOCAL_DB_PATH)
    
    # Jalankan aplikasi Flask
    app.run(host='0.0.0.0', port=8000, debug=True)