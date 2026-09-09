import streamlit as st
import pandas as pd
import gspread

from google.oauth2.service_account import Credentials
from config import get_config
from utils.dates import parse_date_from_columns

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

        worksheet_name = get_config("worksheet_name")
        try:
            return sh.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            available = [w.title for w in sh.worksheets()]
            st.error(f"Worksheet '{worksheet_name}' tidak ditemukan.")
            st.write("Worksheet yang tersedia:", available)
            st.stop()

    except Exception as e:
        st.error("Gagal terhubung ke Google Sheets.")
        st.exception(e)
        st.stop()


def _clean_dataframe(values: list) -> pd.DataFrame:
    """Membersihkan data mentah dari Sheets: header duplikat, panjang baris,
    kolom wajib, normalisasi tipe, parsing tanggal, dan baris kosong."""
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
        data.append(r[: len(unique_headers)])

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
        df["CHECK"].astype(str).str.strip().str.upper().isin(["TRUE", "1", "YES", "YA", "SELESAI"])
    )
    df["NO"] = pd.to_numeric(df["NO"], errors="coerce")
    df["PESERTA"] = pd.to_numeric(df["PESERTA"], errors="coerce").fillna(0).astype(int)

    # 5 & 6. Parsing tanggal efektif (mulai & selesai), pakai utilitas bersama
    df["_TGL_EFEKTIF"] = df.apply(
        lambda row: parse_date_from_columns(row, ["TANGGAL MULAI", "RENCANA MULAI"]), axis=1
    )
    df["_TGL_SELESAI_EFEKTIF"] = df.apply(
        lambda row: parse_date_from_columns(row, ["TANGGAL SELESAI", "RENCANA SELESAI"]), axis=1
    )

    # 7. Bersihkan baris kosong
    mask_empty = (
        df["NO"].isna()
        & df["BIDANG"].astype(str).str.strip().eq("")
        & df["PROGRAM PELATIHAN"].astype(str).str.strip().eq("")
    )
    return df[~mask_empty][COLUMNS + ["_TGL_EFEKTIF", "_TGL_SELESAI_EFEKTIF"]].copy()


@st.cache_data(ttl=get_config("cache_ttl_seconds"))
def load_data() -> pd.DataFrame:
    """Membaca & membersihkan data dari Google Sheets (hasil di-cache beberapa saat)."""
    ws = get_worksheet()
    try:
        values = ws.get_all_values()
    except Exception as e:
        st.error("Gagal membaca data dari Google Sheets.")
        st.exception(e)
        return pd.DataFrame(columns=COLUMNS)
    return _clean_dataframe(values)


def load_data_fresh() -> pd.DataFrame:
    """Sama seperti load_data() tapi selalu mengambil data terbaru langsung dari
    Sheets tanpa cache. Dipakai tepat sebelum operasi tulis (add/update/delete)
    untuk memperkecil risiko menimpa perubahan orang lain (race condition)."""
    ws = get_worksheet()
    try:
        values = ws.get_all_values()
    except Exception as e:
        st.error("Gagal membaca data terbaru dari Google Sheets.")
        st.exception(e)
        return pd.DataFrame(columns=COLUMNS)
    return _clean_dataframe(values)


def _row_dict_to_values(row: dict) -> list:
    """Ubah dict satu baris data menjadi list nilai string sesuai urutan COLUMNS,
    siap ditulis ke Sheets."""
    out = []
    for col in COLUMNS:
        val = row.get(col, "")
        if col == "CHECK":
            out.append("TRUE" if bool(val) else "FALSE")
        elif col == "PESERTA":
            try:
                out.append(str(int(val)))
            except (TypeError, ValueError):
                out.append("0")
        elif col == "NO":
            try:
                out.append("" if pd.isna(val) else str(int(float(val))))
            except (TypeError, ValueError):
                out.append(str(val))
        else:
            out.append("" if val is None else str(val))
    return out


def _find_row_index_by_no(no_value: int):
    """Cari nomor baris (1-based, termasuk header) di worksheet berdasarkan
    kolom NO. Mengembalikan None jika tidak ditemukan."""
    ws = get_worksheet()
    col_values = ws.col_values(COLUMNS.index("NO") + 1)  # kolom NO
    target = str(int(no_value))
    for idx, val in enumerate(col_values, start=1):
        if idx == 1:
            continue  # skip header
        try:
            if str(int(float(val))) == target:
                return idx
        except (TypeError, ValueError):
            continue
    return None


def add_row(row: dict) -> bool:
    """Menambahkan satu baris baru ke akhir sheet (partial write, bukan
    clear+rewrite seluruh sheet)."""
    ws = get_worksheet()
    try:
        ws.append_row(_row_dict_to_values(row), value_input_option="USER_ENTERED")
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error("Gagal menambahkan data baru ke Google Sheets.")
        st.exception(e)
        return False


def update_row(no_value: int, row: dict) -> bool:
    """Update satu baris yang sudah ada (dicari berdasarkan NO), hanya menulis
    ulang baris tersebut, bukan seluruh sheet."""
    ws = get_worksheet()
    try:
        row_idx = _find_row_index_by_no(no_value)
        if row_idx is None:
            st.error(
                f"Baris dengan NO {no_value} tidak ditemukan di Google Sheets "
                "(mungkin sudah diubah/dihapus orang lain). Silakan muat ulang data."
            )
            return False
        last_col_letter = gspread.utils.rowcol_to_a1(1, len(COLUMNS)).rstrip("0123456789")
        cell_range = f"A{row_idx}:{last_col_letter}{row_idx}"
        ws.update(cell_range, [_row_dict_to_values(row)], value_input_option="USER_ENTERED")
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error("Gagal memperbarui data di Google Sheets.")
        st.exception(e)
        return False


def delete_row(no_value: int) -> bool:
    """Menghapus satu baris berdasarkan NO (partial write)."""
    ws = get_worksheet()
    try:
        row_idx = _find_row_index_by_no(no_value)
        if row_idx is None:
            st.error(
                f"Baris dengan NO {no_value} tidak ditemukan di Google Sheets "
                "(mungkin sudah dihapus orang lain). Silakan muat ulang data."
            )
            return False
        ws.delete_rows(row_idx)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error("Gagal menghapus data di Google Sheets.")
        st.exception(e)
        return False


def save_data(df_to_save: pd.DataFrame) -> bool:
    """Menyimpan seluruh DataFrame kembali ke worksheet (bulk overwrite).

    Dipertahankan untuk operasi massal (mis. import ulang data), TAPI kini
    dengan backup + rollback: kalau penulisan gagal di tengah jalan, data lama
    dikembalikan alih-alih dibiarkan kosong. Untuk operasi tambah/edit/hapus
    satu baris sehari-hari, gunakan add_row / update_row / delete_row di atas
    karena jauh lebih cepat dan lebih aman.
    """
    ws = get_worksheet()

    # 1. Backup data lama dulu, sebelum melakukan perubahan apa pun
    try:
        backup_values = ws.get_all_values()
    except Exception as e:
        st.error("Gagal membuat backup sebelum menyimpan. Penyimpanan dibatalkan demi keamanan data.")
        st.exception(e)
        return False

    try:
        df_out = df_to_save.copy()
        for col in COLUMNS:
            if col not in df_out.columns:
                df_out[col] = False if col == "CHECK" else (0 if col == "PESERTA" else "")
        df_out = df_out[COLUMNS]

        rows = [COLUMNS] + [_row_dict_to_values(r) for r in df_out.to_dict("records")]

        ws.clear()
        ws.update(rows, "A1")
        st.cache_data.clear()
        return True

    except Exception as e:
        st.error("Gagal menyimpan data ke Google Sheets. Mencoba mengembalikan data sebelumnya...")
        st.exception(e)
        try:
            ws.clear()
            if backup_values:
                ws.update(backup_values, "A1")
            st.warning("Data berhasil dikembalikan ke kondisi sebelum penyimpanan gagal.")
        except Exception as rollback_error:
            st.error("GAGAL mengembalikan data lama. Segera hubungi admin/periksa Google Sheets secara manual.")
            st.exception(rollback_error)
        return False