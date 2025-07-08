import os
import uuid
import base64
from flask import Flask, request, jsonify
from deepface import DeepFace
import pandas as pd
from gcs_handler import synchronize_gcs_to_local, upload_face_to_gcs, LOCAL_DB_PATH

app = Flask(__name__)

# --- Konfigurasi ---
MODEL_NAME = "VGG-Face"
DISTANCE_METRIC = "cosine"
DISTANCE_THRESHOLD = 0.6
UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

UNRECOGNIZED_MESSAGE = "wajah anda tidak saya kenali silahkan daftarkan wajah anda"

@app.route('/recognize', methods=['POST'])
def recognize_face():
    synchronize_gcs_to_local()

    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada file gambar dalam permintaan"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Nama file kosong"}), 400

    if file:
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        temp_image_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_image_path)

        try:
            dfs = DeepFace.find(
                img_path=temp_image_path,
                db_path=LOCAL_DB_PATH,
                model_name=MODEL_NAME,
                distance_metric=DISTANCE_METRIC,
                enforce_detection=False
            )

            if not dfs or dfs[0].empty:
                print("Wajah tidak ditemukan di database atau tidak ada kecocokan.")
                return jsonify({"status": "unrecognized", "message": UNRECOGNIZED_MESSAGE})

            result_df = dfs[0]
            best_match = result_df.iloc[0]
            distance_column_name = [col for col in result_df.columns if DISTANCE_METRIC in col]

            if not distance_column_name:
                if 'distance' in result_df.columns:
                    distance_column_name = ['distance']
                else:
                    raise KeyError(f"Tidak dapat menemukan kolom jarak. Kolom yang tersedia: {list(result_df.columns)}")

            distance = best_match[distance_column_name[0]]

            if distance <= DISTANCE_THRESHOLD:
                identity_path = best_match['identity']
                person_name = os.path.basename(os.path.dirname(identity_path))
                if person_name == LOCAL_DB_PATH:
                    person_name = os.path.splitext(os.path.basename(identity_path))[0]

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
            if "Face could not be detected" in str(e):
                return jsonify({"status": "error", "message": "Tidak ada wajah yang terdeteksi di gambar."})
            return jsonify({"status": "error", "message": f"Terjadi kesalahan internal: {str(e)}"})
        finally:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)

    return jsonify({"status": "error", "message": "Terjadi kesalahan yang tidak diketahui."}), 500


@app.route('/register', methods=['POST'])
def register_face():
    data = request.get_json()
    if not data or 'name' not in data or 'image' not in data:
        return jsonify({"status": "error", "message": "Permintaan tidak valid. 'name' dan 'image' diperlukan."}), 400

    person_name = data['name']
    image_data = data['image']

    try:
        image_bytes = base64.b64decode(image_data)
        filename = f"{person_name}_{uuid.uuid4()}.jpg"
        temp_image_path = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(temp_image_path, 'wb') as f:
            f.write(image_bytes)

        success = upload_face_to_gcs(temp_image_path, person_name)

        if success:
            print("Memperbarui database lokal setelah pendaftaran baru...")
            synchronize_gcs_to_local()
            return jsonify({"status": "success", "message": f"Wajah untuk {person_name} berhasil didaftarkan."})
        else:
            return jsonify({"status": "error", "message": "Gagal mengunggah gambar ke GCS."}), 500

    except Exception as e:
        print(f"Error selama pendaftaran: {e}")
        return jsonify({"status": "error", "message": f"Terjadi kesalahan internal: {str(e)}"}), 500
    finally:
        if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
            os.remove(temp_image_path)


@app.route('/compare_models', methods=['POST'])
def compare_models():
    MODELS = ["ArcFace", "Facenet", "VGG-Face"]
    DISTANCE_METRIC = "cosine"
    DISTANCE_THRESHOLD = 0.6

    synchronize_gcs_to_local()

    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada file gambar dalam permintaan"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Nama file kosong"}), 400

    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    temp_image_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(temp_image_path)

    results = {}

    try:
        for model_name in MODELS:
            try:
                dfs = DeepFace.find(
                    img_path=temp_image_path,
                    db_path=LOCAL_DB_PATH,
                    model_name=model_name,
                    distance_metric=DISTANCE_METRIC,
                    enforce_detection=False
                )

                if not dfs or dfs[0].empty:
                    results[model_name] = {
                        "status": "unrecognized",
                        "message": UNRECOGNIZED_MESSAGE
                    }
                    continue

                result_df = dfs[0]
                best_match = result_df.iloc[0]

                distance_column_name = [col for col in result_df.columns if DISTANCE_METRIC in col]
                if not distance_column_name:
                    distance_column_name = ['distance'] if 'distance' in result_df.columns else []
                if not distance_column_name:
                    results[model_name] = {"status": "error", "message": "Kolom jarak tidak ditemukan"}
                    continue

                distance = best_match[distance_column_name[0]]

                if distance <= DISTANCE_THRESHOLD:
                    identity_path = best_match['identity']
                    person_name = os.path.basename(os.path.dirname(identity_path))
                    if person_name == LOCAL_DB_PATH:
                        person_name = os.path.splitext(os.path.basename(identity_path))[0]

                    confidence_score = (1 - distance) * 100

                    results[model_name] = {
                        "status": "recognized",
                        "name": person_name,
                        "distance": float(distance),
                        "confidence": f"{confidence_score:.2f}%"
                    }
                else:
                    results[model_name] = {
                        "status": "unrecognized",
                        "message": f"Jarak terlalu jauh: {distance:.4f}"
                    }
            except Exception as model_err:
                results[model_name] = {
                    "status": "error",
                    "message": f"Gagal memproses model {model_name}: {str(model_err)}"
                }

        return jsonify({
            "status": "success",
            "models": results
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Terjadi kesalahan internal: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)


if __name__ == '__main__':
    if not os.path.exists(LOCAL_DB_PATH):
        os.makedirs(LOCAL_DB_PATH)
    
    app.run(host='0.0.0.0', port=8000, debug=True)
