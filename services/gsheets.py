import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

WORKSHEET_NAME = "Reg"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

COLUMNS = [
    "NO",
    "BIDANG",
    "PROGRAM PELATIHAN",
    "CHECK",
    "PESERTA",
    "LOKASI",
    "TANGGAL MULAI",
    "TANGGAL SELESAI",
    "RENCANA MULAI",
    "RENCANA SELESAI",
    "KETERANGAN",
]


@st.cache_resource
def get_worksheet():
    """Koneksi ke spreadsheet dan worksheet menggunakan credentials dari secrets.toml."""
    try:
        secrets = dict(st.secrets["connections"]["gsheets"])
        spreadsheet_url = secrets.pop("spreadsheet")
        secrets.pop("worksheet", None)

        creds = Credentials.from_service_account_info(secrets, scopes=SCOPES)
        client = gspread.authorize(creds)
        sh = client.open_by_url(spreadsheet_url)

        try:
            return sh.worksheet(WORKSHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            available = [w.title for w in sh.worksheets()]
            st.error(f"Worksheet '{WORKSHEET_NAME}' tidak ditemukan.")
            st.write("Worksheet yang tersedia:", available)
            st.stop()

    except Exception as e:
        st.error("Gagal terhubung ke Google Sheets.")
        st.exception(e)
        st.stop()


@st.cache_data(ttl=10)
def load_data():
    """
    Membaca data dari Google Sheets dengan penanganan header duplikat,
    normalisasi tipe data, dan parsing tanggal efektif (mulai & selesai).
    """
    ws = get_worksheet()
    try:
        values = ws.get_all_values()
    except Exception as e:
        st.error("Gagal membaca data dari Google Sheets.")
        st.exception(e)
        return pd.DataFrame(columns=COLUMNS)

    if not values:
        return pd.DataFrame(columns=COLUMNS)

    # 1. Sanitasi header ganda agar tidak crash di Pandas
    headers = [str(h).strip() for h in values[0]]
    seen = {}
    unique_headers = []

    for h in headers:
        h = h or "KOLOM"
        if h not in seen:
            seen[h] = 1
            unique_headers.append(h)
        else:
            seen[h] += 1
            unique_headers.append(f"{h}_{seen[h]}")

    # 2. Normalisasi panjang baris
    data = []
    for r in values[1:]:
        r = list(r)
        if len(r) < len(unique_headers):
            r += [""] * (len(unique_headers) - len(r))
        data.append(r[:len(unique_headers)])

    df = pd.DataFrame(data, columns=unique_headers)

    # 3. Pastikan semua kolom utama tersedia
    for col in COLUMNS:
        if col not in df.columns:
            if col == "CHECK":
                df[col] = False
            elif col == "PESERTA":
                df[col] = 0
            else:
                df[col] = ""

    # 4. Normalisasi data boolean dan numerik
    df["CHECK"] = (
        df["CHECK"]
        .astype(str)
        .str.strip()
        .str.upper()
        .isin(["TRUE", "1", "YES", "YA", "SELESAI"])
    )
    df["NO"] = pd.to_numeric(df["NO"], errors="coerce")
    df["PESERTA"] = pd.to_numeric(df["PESERTA"], errors="coerce").fillna(0).astype(int)

    # 5. Parsing Tanggal Mulai Efektif (untuk grafik bulanan)
    def parse_tgl_mulai(row):
        for col in ["TANGGAL MULAI", "RENCANA MULAI"]:
            val = str(row.get(col, "")).strip()
            if val:
                for fmt in ["%d %b %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                    try:
                        return datetime.strptime(val, fmt).date()
                    except Exception:
                        pass
        return None

    # 6. Parsing Tanggal Selesai Efektif (untuk deteksi peringatan survei H-10)
    def parse_tgl_selesai(row):
        for col in ["TANGGAL SELESAI", "RENCANA SELESAI"]:
            val = str(row.get(col, "")).strip()
            if val:
                for fmt in ["%d %b %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                    try:
                        return datetime.strptime(val, fmt).date()
                    except Exception:
                        pass
        return None

    df["_TGL_EFEKTIF"] = df.apply(parse_tgl_mulai, axis=1)
    df["_TGL_SELESAI_EFEKTIF"] = df.apply(parse_tgl_selesai, axis=1)

    # 7. Bersihkan baris kosong
    mask_empty = (
        df["NO"].isna()
        & df["BIDANG"].astype(str).str.strip().eq("")
        & df["PROGRAM PELATIHAN"].astype(str).str.strip().eq("")
    )
    return df[~mask_empty][COLUMNS + ["_TGL_EFEKTIF", "_TGL_SELESAI_EFEKTIF"]].copy()


def save_data(df_to_save: pd.DataFrame):
    """Menyimpan seluruh DataFrame kembali ke worksheet 'Reg' di Google Sheets."""
    ws = get_worksheet()
    try:
        df_out = df_to_save.copy()

        for col in COLUMNS:
            if col not in df_out.columns:
                if col == "CHECK":
                    df_out[col] = False
                elif col == "PESERTA":
                    df_out[col] = 0
                else:
                    df_out[col] = ""

        df_out = df_out[COLUMNS]

        # Format boolean CHECK menjadi string yang dikenali
        df_out["CHECK"] = df_out["CHECK"].apply(lambda v: "TRUE" if bool(v) else "FALSE")
        df_out["PESERTA"] = pd.to_numeric(df_out["PESERTA"], errors="coerce").fillna(0).astype(int)

        def format_no(value):
            try:
                if pd.isna(value):
                    return ""
                return str(int(float(value)))
            except Exception:
                return str(value)

        df_out["NO"] = df_out["NO"].apply(format_no)
        df_out = df_out.fillna("")

        rows = [COLUMNS] + df_out.astype(str).values.tolist()

        ws.clear()
        ws.update(rows, "A1")

        # Bersihkan cache agar data baru langsung terbaca
        st.cache_data.clear()

    except Exception as e:
        st.error("Gagal menyimpan data ke Google Sheets.")
        st.exception(e)