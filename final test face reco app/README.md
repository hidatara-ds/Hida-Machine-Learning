# Aplikasi API Pengenalan Wajah dengan Flask dan Google Cloud Storage

Aplikasi ini adalah sebuah API berbasis Flask yang menyediakan layanan untuk mengenali dan mendaftarkan wajah. Aplikasi ini menggunakan `deepface` untuk analisis wajah dan Google Cloud Storage (GCS) sebagai database untuk menyimpan gambar wajah.

## Fitur

-   **Sinkronisasi Otomatis:** Secara otomatis mengunduh database wajah dari GCS saat pertama kali dijalankan.
-   **Endpoint `/recognize`**: Menerima file gambar dan mengembalikan nama orang yang paling cocok dari database, beserta `distance` dan `confidence score`.
-   **Endpoint `/register`**: Menerima nama dan file gambar (base64) untuk mendaftarkan wajah baru ke dalam database GCS.

---

## Prasyarat

Sebelum memulai, pastikan kamu sudah memiliki:
1.  **Python 3.10**. Versi ini penting untuk kompatibilitas dengan `tensorflow==2.11.0`.
2.  Akun Google Cloud Platform (GCP) dengan sebuah **Bucket GCS** yang sudah dibuat.

---

## Panduan Instalasi dan Setup

Ikuti langkah-langkah berikut untuk menjalankan aplikasi di komputermu.

### 1. Clone Repository (jika belum)
```bash
git clone <URL_REPOSITORY_ANDA>
cd <NAMA_FOLDER_REPOSITORY>/final test face reco app
```

### 2. Konfigurasi Google Cloud
-   **Buat Service Account** di GCP dan unduh file kredensialnya.
-   **Ubah nama file** kredensial yang diunduh menjadi `key.json`.
-   **Letakkan `key.json`** di dalam folder `final test face reco app/`, sejajar dengan `app.py`.

### 3. Atur Nama Bucket GCS
-   Buka file `gcs_handler.py`.
-   Ubah nilai variabel `GCS_BUCKET_NAME` dengan nama bucket GCS yang sudah kamu siapkan.
    ```python
    # gcs_handler.py
    GCS_BUCKET_NAME = "nama-bucket-kamu" 
    ```

### 4. Buat dan Aktifkan Virtual Environment
-   Buka terminal di dalam folder `final test face reco app`.
-   Gunakan **Python 3.10** untuk membuat virtual environment:
    ```bash
    # Untuk Windows (jika punya Python Launcher)
    py -3.10 -m venv venv

    # Untuk Linux/macOS atau jika 'python3.10' ada di PATH
    python3.10 -m venv venv
    ```
-   Aktifkan virtual environment:
    ```bash
    # Windows (PowerShell)
    .\venv\Scripts\Activate

    # Linux/macOS
    source venv/bin/activate
    ```
    Kamu akan melihat `(venv)` di awal baris terminalmu.

### 5. Install Semua Dependencies
-   Pastikan file `requirements.txt` sudah ada.
-   Jalankan perintah berikut untuk meng-install semua package yang dibutuhkan:
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

---

## Cara Menjalankan Aplikasi

### Langkah 1: Jalankan Server API
-   Di terminal yang sama (dengan `venv` aktif), jalankan server Flask:
    ```bash
    python app.py
    ```
-   Server akan mulai berjalan dan melakukan sinkronisasi dengan GCS. Biarkan terminal ini tetap terbuka.

### Langkah 2: Jalankan Client untuk Tes
-   Buka **terminal baru**.
-   Masuk ke direktori `final test face reco app` dan **aktifkan venv** yang sama seperti di langkah sebelumnya.
    ```bash
    # Windows (PowerShell)
    cd "path/to/final test face reco app"
    .\venv\Scripts\Activate
    ```
-   Jalankan script `test_client.py` untuk mengirim request ke server:
    ```bash
    python test_client.py
    ```
-   Kamu akan melihat output sapaan di terminal client, dan log request di terminal server.

**Untuk Mengetes Gambar Lain:**
-   Buka file `test_client.py`.
-   Ubah path gambar di variabel `image_to_recognize`.
-   Simpan file dan jalankan ulang `python test_client.py`.

---
## Struktur File Penting
-   `app.py`: Logika utama server Flask dan endpoint API.
-   `gcs_handler.py`: Fungsi untuk sinkronisasi dan upload ke Google Cloud Storage.
-   `test_client.py`: Script untuk mengetes endpoint API.
-   `requirements.txt`: Daftar semua package Python yang dibutuhkan.
-   `key.json`: File kredensial rahasia untuk mengakses GCP (JANGAN DI-UPLOAD KE GIT).
-   `gcs_database/`: Folder lokal tempat database wajah dari GCS disimpan.
-   `temp_uploads/`: Folder sementara untuk gambar yang di-upload saat proses pengenalan. 