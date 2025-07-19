import os
import logging
import tempfile
from flask import Flask, request, jsonify
from deepface import DeepFace

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "database")

if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)
    logging.info(f"Folder database dibuat di: {DB_PATH}")
if not os.listdir(DB_PATH):
    logging.warning("Folder database kosong! Aplikasi tidak akan dapat mengenali wajah.")

@app.route("/")
def index():
    return "Face Recognition API siap digunakan. Kirim POST request ke /recognize."

@app.route('/recognize', methods=['POST'])
def recognize_face():
    if 'file' not in request.files:
        return jsonify({"error": "Request harus berisi 'file' gambar"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Tidak ada file yang dipilih"}), 400

    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, file.filename)
    file.save(temp_file_path)
    logging.info(f"File sementara disimpan di: {temp_file_path}")

    try:
        # Menambahkan print() untuk debugging, ini akan tampil di terminal server Flask
        logging.info("Mencari wajah di database...")
        dfs = DeepFace.find(
            img_path=temp_file_path,
            db_path=DB_PATH,
            model_name="VGG-Face",
            enforce_detection=False
        )
        
        # dfs adalah list of DataFrame. Kita cek isinya.
        logging.info(f"Hasil dari DeepFace.find(): {dfs}")

        if not dfs or dfs[0].empty:
            logging.info("Tidak ada wajah yang cocok ditemukan di database.")
            return jsonify({"status": "unknown", "message": "Wajah tidak dikenali."})

        # Ambil hasil teratas
        top_result = dfs[0].iloc[0]
        identity_path = top_result['identity']
        file_name = os.path.basename(identity_path)
        name = os.path.splitext(file_name)[0]
        
        distance = top_result['distance']
        # -----------------------------
        
        confidence_level = (1 - distance) * 100

        logging.info(f"Wajah teridentifikasi sebagai: {name} dengan confidence: {confidence_level:.2f}%")
        return jsonify({
            "status": "recognized",
            "name": name,
            "confidence": f"{confidence_level:.2f}%"
        })

    except Exception as e:
        logging.error(f"Terjadi error saat pemrosesan: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logging.info(f"File sementara dihapus: {temp_file_path}")

if __name__ == '__main__':
    # Ganti port jika perlu
    app.run(host='0.0.0.0', port=8081)