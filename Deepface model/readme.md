# Face Recognition API with DeepFace on Google Compute Engine

API sederhana berbasis Flask untuk mengenali wajah menggunakan DeepFace. Aplikasi ini menerima gambar wajah dan membandingkannya dengan database wajah yang telah disiapkan, lalu mengembalikan hasil pengenalan dalam format JSON.

---

## 📌 Fitur

- Menggunakan DeepFace (model VGG-Face) untuk face recognition
- Dibuat dengan Flask dan siap untuk deployment di Google Compute Engine (GCE)
- Mendukung pengiriman gambar lewat endpoint POST `/recognize`
- Memberikan nama dan tingkat kemiripan (confidence) wajah yang dikenali

---

## 🧱 Struktur Folder

face-recognition-app/
├── app.py # Aplikasi utama Flask
├── requirements.txt # Daftar dependensi Python
└── database/ # Folder database wajah
├── ronaldo.jpg
├── messi.jpg
└── _placeholder.txt # File kosong agar folder bisa di-commit


---

## 🛠️ Tahapan Pengerjaan

### 1. Membangun Aplikasi di Komputer Lokal

#### 1.1 Persiapan Virtual Environment (Opsional tapi disarankan)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 1.2 Instalasi Library
```bash
pip install -r requirements.txt
```
#### 1.3 Jalankan Aplikasi
```bash
flask run --host=0.0.0.0 --port=8080
```
⚠️ Pada awal dijalankan, DeepFace akan mengunduh model-model yang diperlukan.

#### 1.4 Uji Coba di Lokal
Kirim gambar menggunakan curl:
```bash
curl -X POST -F "file=@/path/to/your/test_ronaldo.jpg" http://127.0.0.1:8080/recognize
```

### 2. Deployment di Google Compute Engine

#### 2.1 Persiapan Instance GCE

1. Buka Google Cloud Console dan buat project baru.
2. Aktifkan API Compute Engine dan Cloud Storage.
3. Buat instance GCE dengan konfigurasi yang sesuai (misalnya, menggunakan Ubuntu 20.04).

#### 2.2 Konfigurasi Firewall

- Buka firewall untuk port 8080 pada instance GCE.

#### 2.3 Konfigurasi SSH

```bash
curl -X POST -F "file=@/path/to/your/test_ronaldo.jpg" http://127.0.0.1:8080/recognize
``` 