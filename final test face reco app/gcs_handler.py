# gcs_handler.py
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.path.dirname(__file__), "key.json")
from google.cloud import storage
from google.api_core.exceptions import NotFound

# Konfigurasi GCS
# Ganti dengan nama bucket GCS Anda
GCS_BUCKET_NAME = "face-recognition-db" 
# Direktori lokal untuk menyimpan database wajah yang disinkronkan
LOCAL_DB_PATH = "gcs_database" 

def synchronize_gcs_to_local():
    """
    Mengunduh seluruh isi bucket GCS ke direktori lokal.
    Fungsi ini mereplikasi struktur folder dari GCS.
    Ini harus dipanggil saat aplikasi dimulai.
    """
    print(f"Memulai sinkronisasi dari GCS bucket: {GCS_BUCKET_NAME} ke direktori lokal: {LOCAL_DB_PATH}")
    
    # Inisialisasi klien GCS
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
    except Exception as e:
        print(f"Error: Gagal menginisialisasi klien GCS atau mengakses bucket. Pastikan kredensial sudah diatur. Detail: {e}")
        return

    # Periksa apakah direktori lokal sudah ada dan berisi file. Jika ya, lewati sinkronisasi.
    if os.path.exists(LOCAL_DB_PATH) and len(os.listdir(LOCAL_DB_PATH)) > 0:
        print("Direktori lokal sudah ada dan tidak kosong. Melewati sinkronisasi.")
        # Hapus file cache representasi jika ada untuk memaksa DeepFace membangunnya kembali
        # Ini penting jika ada perubahan di GCS sejak terakhir kali dijalankan.
        pkl_file = os.path.join(LOCAL_DB_PATH, "representations_vgg_face.pkl")
        if os.path.exists(pkl_file):
            print("Menghapus file cache representasi lama...")
            os.remove(pkl_file)
        return

    print("Direktori lokal kosong. Memulai pengunduhan dari GCS...")
    
    # Buat direktori lokal jika belum ada
    if not os.path.exists(LOCAL_DB_PATH):
        os.makedirs(LOCAL_DB_PATH)

    blobs = bucket.list_blobs()
    download_count = 0
    for blob in blobs:
        # Buat jalur file lokal yang sesuai dengan struktur di GCS
        destination_file_path = os.path.join(LOCAL_DB_PATH, blob.name)
        
        # Buat direktori induk jika belum ada
        destination_dir = os.path.dirname(destination_file_path)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
            
        # Unduh blob ke file lokal
        try:
            print(f"Mengunduh {blob.name} ke {destination_file_path}...")
            blob.download_to_filename(destination_file_path)
            download_count += 1
        except Exception as e:
            print(f"Error: Gagal mengunduh file {blob.name}. Detail: {e}")

    print(f"Sinkronisasi selesai. Total {download_count} file diunduh.")


def upload_face_to_gcs(image_path, person_name):
    """
    Mengunggah file gambar ke GCS di bawah folder nama orang tersebut.
    
    Args:
        image_path (str): Jalur ke file gambar lokal yang akan diunggah.
        person_name (str): Nama orang, digunakan sebagai nama folder di GCS.

    Returns:
        bool: True jika berhasil, False jika gagal.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        # Tentukan nama file unik untuk menghindari tumpang tindih
        file_name = os.path.basename(image_path)
        destination_blob_name = f"{person_name}/{file_name}"
        
        blob = bucket.blob(destination_blob_name)
        
        print(f"Mengunggah {image_path} ke GCS di gs://{GCS_BUCKET_NAME}/{destination_blob_name}")
        blob.upload_from_filename(image_path)
        print("Unggahan berhasil.")
        return True
    except Exception as e:
        print(f"Error: Gagal mengunggah file ke GCS. Detail: {e}")
        return False