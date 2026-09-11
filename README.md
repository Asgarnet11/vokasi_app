# Monitoring Program Pelatihan Vokasi — BPVP Kendari

Dashboard pemantauan, pengelolaan data, dan kapasitas program pelatihan vokasi berbasis **Streamlit** yang terhubung dua arah (_real-time read & write_) ke **Google Sheets**.

---

## Fitur Utama

1. **Sistem Tema Hybrid (Sun / Light & Moon / Dark)**
   Pengalihan mode terang dan gelap langsung lewat _toggle_ di sidebar, tanpa konflik warna teks maupun kontras grafik.

2. **Dashboard Target & Capaian Kuota Pelatihan**
   - Kartu metrik utama dengan capaian siswa 0–100%.
   - Kartu hierarki kuota per **Kejuruan (Bidang)**, lengkap dengan rincian program di dalamnya.

3. **Visualisasi Berorientasi Horizontal**
   - **Grafik Kuota Siswa per Kejuruan** — batang horizontal untuk membandingkan kapasitas tiap jurusan.
   - **Grafik Sebaran Jadwal** — visualisasi bulanan berbasis tanggal efektif program.

4. **Peringatan Dini Survei Pelatihan (Notifikasi H-10)**
   Banner otomatis untuk program yang berada ≤ 10 hari menuju akhir masa pelatihan, agar siswa segera diarahkan mengisi survei/evaluasi.

5. **Kelola Data Interaktif**
   - Tabel data dengan multi-filter (Bidang, Program, Lokasi, Status Selesai).
   - Tambah, edit, dan hapus baris — langsung tersinkron ke Google Sheets.

---

## Struktur Data Google Sheets

Worksheet wajib bernama **`Reg`**, dengan header berikut di baris pertama:

| Kolom               | Tipe Data | Keterangan                                             |
| ------------------- | --------- | ------------------------------------------------------ |
| `NO`                | Numerik   | Nomor indeks baris                                     |
| `BIDANG`            | Teks      | Nama kejuruan (mis. _Teknologi Informasi_, _Otomotif_) |
| `PROGRAM PELATIHAN` | Teks      | Nama kelas pelatihan vokasi                            |
| `CHECK`             | Boolean   | Status selesai (`TRUE`/`FALSE` atau `1`/`0`)           |
| `PESERTA`           | Numerik   | Jumlah kuota siswa yang terdaftar/terisi               |
| `LOKASI`            | Teks      | Tempat pelaksanaan (mis. _BPVP Kendari_, _LPK_, _BLK_) |
| `TANGGAL MULAI`     | Tanggal   | Format: `DD MMM YYYY` (contoh: `12 Jan 2026`)          |
| `TANGGAL SELESAI`   | Tanggal   | Format: `DD MMM YYYY`                                  |
| `RENCANA MULAI`     | Tanggal   | Tanggal estimasi mulai                                 |
| `RENCANA SELESAI`   | Tanggal   | Tanggal estimasi selesai                               |
| `KETERANGAN`        | Teks      | Catatan tambahan program                               |

---

## Instalasi & Pengaturan Lokal

### 1. Kloning repositori & instal dependensi

```bash
git clone <URL_REPOSITORY_ANDA>
cd Dashboard-Pelatihan-Vokasi
pip install -r requirements.txt
```

Pastikan `requirements.txt` berisi dependensi berikut:

```
streamlit>=1.35.0
pandas>=2.0.0
plotly>=5.18.0
gspread>=6.0.0
google-auth>=2.20.0
```

### 2. Konfigurasi Google Service Account

1. Buka [Google Cloud Console](https://console.cloud.google.com/) dan buat proyek baru.
2. Aktifkan **Google Sheets API** dan **Google Drive API**.
3. Masuk ke **IAM & Admin → Service Accounts → Create Service Account**.
4. Buka akun yang baru dibuat → tab **Keys → Add Key → Create New Key (JSON)** → simpan berkas kuncinya.
5. Buka spreadsheet Google Sheets Anda, klik **Share**, lalu tempelkan alamat surel `client_email` dari berkas JSON tersebut dengan peran **Editor**.

### 3. Pengaturan kredensial (`secrets.toml`)

Buat folder `.streamlit` di direktori utama proyek, lalu buat berkas `secrets.toml` di dalamnya:

```bash
mkdir -p .streamlit
touch .streamlit/secrets.toml
```

Isi `.streamlit/secrets.toml` dengan konfigurasi akun layanan Anda:

```toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/<ID_SPREADSHEET_ANDA>/edit"

type = "service_account"
project_id = "monitoring-vokasi"
private_key_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "xxxxxx@monitoring-vokasi.iam.gserviceaccount.com"
client_id = "xxxxxxxxxxxxxxxxxxxx"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/xxxxxx"
```

> **Peringatan:** Jangan pernah menambahkan `secrets.toml` ke repositori publik Git. Pastikan `.streamlit/secrets.toml` tercantum di `.gitignore`.

### 4. Menjalankan dashboard

```bash
streamlit run app.py
```

Buka peramban di [http://localhost:8501](http://localhost:8501).

---

## Panduan Deployment (Streamlit Community Cloud)

1. Unggah kode ke repositori GitHub Anda.
2. Kunjungi [share.streamlit.io](https://share.streamlit.io) dan masuk dengan akun GitHub.
3. Pilih repositori, cabang (_branch_), dan tentukan berkas utama ke `app.py`.
4. Buka menu **Advanced settings → Secrets**.
5. Salin seluruh isi `.streamlit/secrets.toml` lokal Anda, lalu tempelkan ke kolom isian tersebut.
6. Klik **Deploy** — dashboard siap digunakan bersama tim secara live.

---

## Arsitektur Berkas

```
├── .streamlit/
│   └── secrets.toml          # Kredensial koneksi Google Sheets (rahasia)
├── components/
│   ├── dashboard_view.py     # Logika kartu metrik, notifikasi H-10, & grafik Plotly
│   ├── data_table.py         # Tabel data HTML custom mengikuti tema aktif
│   └── theme.py              # Injeksi CSS dinamis & token palet Hybrid
├── services/
│   └── gsheets.py            # Autentikasi gspread, caching, & sanitasi data
├── utils/
│   └── dates.py              # Parsing & formatting tanggal terpusat
├── config.py                 # Konfigurasi aplikasi (bisa dioverride via secrets)
├── app.py                    # Entry point aplikasi & orkestrasi tampilan halaman
├── requirements.txt          # Dependensi pustaka Python
└── README.md                 # Dokumentasi panduan operasional
```

---

## Kredit & Kontributor

| Nama                     | Peran                                           | GitHub                                       |
| ------------------------ | ----------------------------------------------- | -------------------------------------------- |
| **Argita Trihapsari**    | Pembuat pertama / inisiator proyek `vokasi_app` | [@Argittt](https://github.com/Argittt)       |
| **Muh Asgar Fatwahyudi** | Pengembangan lanjutan & perbaikan               | [@Asgarnet11](https://github.com/Asgarnet11) |
