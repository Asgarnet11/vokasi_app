# Monitoring Program Pelatihan Vokasi — Streamlit App

Dashboard, tabel data, dan form edit — semua terhubung **live** ke Google Sheets kamu (baca & tulis dua arah).

## Struktur data yang dibutuhkan di Google Sheets

Buat/pastikan ada sheet bernama **`Data`** dengan kolom header persis seperti ini di baris 1:

```
NO | BIDANG | PROGRAM PELATIHAN | CHECK | LOKASI | TANGGAL MULAI | TANGGAL SELESAI | RENCANA MULAI | RENCANA SELESAI | KETERANGAN
```

(File `data_untuk_looker.xlsx` yang sudah dibuat sebelumnya bisa langsung dipakai — upload ke Drive, buka dengan Sheets, hapus kolom "SELESAI" bantuannya kalau tidak dipakai.)

## Setup (sekali saja)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Buat Service Account di Google Cloud**
   - Buka [console.cloud.google.com](https://console.cloud.google.com) → buat project (atau pakai yang ada).
   - Aktifkan **Google Sheets API** dan **Google Drive API**.
   - Ke *IAM & Admin* → *Service Accounts* → *Create Service Account*.
   - Setelah dibuat, buka service account itu → tab *Keys* → *Add Key* → *Create new key* → pilih **JSON** → download.

3. **Share spreadsheet kamu ke service account**
   - Buka file JSON yang didownload, cari `client_email` (formatnya `xxx@xxx.iam.gserviceaccount.com`).
   - Di Google Sheets kamu, klik **Bagikan** → paste email itu → beri akses **Editor**.

4. **Isi secrets.toml**
   - Copy `.streamlit/secrets.toml.example` jadi `.streamlit/secrets.toml`.
   - Isi `spreadsheet` dengan URL sheet kamu.
   - Isi sisanya dari file JSON service account tadi (field-nya sama persis namanya).

5. **Jalankan**
   ```bash
   streamlit run app.py
   ```

## Fitur

- **Dashboard** — card otomatis per BIDANG (mengikuti data, tidak perlu di-set manual), format `x/y`, progress bar, warna hijau kalau 100% selesai, abu-abu kalau belum ada paket.
- **Lihat Data** — tabel dengan filter Bidang / Program / Lokasi / Status, plus aksi Edit & Hapus per baris.
- **Edit Data** — form tambah/edit satu paket pelatihan, langsung tersimpan ke Google Sheets saat klik Simpan.

## Deploy online (opsional)

Kalau mau dashboard ini bisa diakses tim tanpa perlu jalanin di laptop:
1. Push folder ini ke repo GitHub (jangan ikut commit `secrets.toml` asli — sudah ada di `.gitignore`).
2. Buka [share.streamlit.io](https://share.streamlit.io) → New app → hubungkan ke repo.
3. Di *Advanced settings* → *Secrets*, paste isi `secrets.toml` kamu.
4. Deploy — dapat link publik yang auto-update setiap ada perubahan di Google Sheets.
