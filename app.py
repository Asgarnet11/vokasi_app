# pyrefly: ignore[missing-import]
import streamlit as st
import pandas as pd
from datetime import datetime, date

from services.gsheets import load_data, load_data_fresh, add_row, update_row, delete_row, toggle_check_row, COLUMNS
from components.theme import apply_theme
from components.dashboard_view import render_dashboard
from components.data_table import render_data_table_html
from utils.dates import parse_date, format_date
from utils.exporter import export_monitoring_excel
from config import get_config

# ============================================================
# Konfigurasi Halaman & Tema
# ============================================================
st.set_page_config(
    page_title="Monitoring Program Pelatihan Vokasi",
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "app_theme" not in st.session_state:
    st.session_state["app_theme"] = "moon"
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "dashboard"
if "edit_no" not in st.session_state:
    st.session_state["edit_no"] = None
if "confirm_delete_no" not in st.session_state:
    st.session_state["confirm_delete_no"] = None
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

c_theme = apply_theme(st.session_state["app_theme"])

PAGES = {
    "dashboard": (":material/monitoring:", "Dashboard"),
    "lihat": (":material/table_rows:", "Lihat Data"),
    "edit": (":material/edit_note:", "Tambah / Edit Data"),
}


def go_to(page_key: str):
    st.session_state["active_page"] = page_key


# ============================================================
# Dialog Konfirmasi Hapus
# ============================================================
@st.dialog("Konfirmasi Hapus Data")
def confirm_delete_dialog(no_value: int, nama_program: str):
    st.warning(
        f"Yakin ingin menghapus program **{nama_program}** (NO {no_value})? "
        "Tindakan ini **tidak bisa dibatalkan**."
    )
    c1, c2 = st.columns(2)
    if c1.button("Batal", width="stretch"):
        st.session_state["confirm_delete_no"] = None
        st.rerun()
    if c2.button("Ya, Hapus", width="stretch", type="primary"):
        with st.spinner("Menghapus data..."):
            success = delete_row(no_value)
        st.session_state["confirm_delete_no"] = None
        if success:
            st.toast(f"Baris NO {no_value} berhasil dihapus.", icon=":material/check_circle:")
        st.rerun()


# ============================================================
# Sidebar: Navigasi, Tema & Filter
# ============================================================
with st.sidebar:
    st.markdown("#### Navigasi")
    page_keys = list(PAGES.keys())
    page_labels = [f"{PAGES[k][1]}" for k in page_keys]
    current_idx = page_keys.index(st.session_state["active_page"])
    chosen_label = st.radio(
        "Halaman", page_labels, index=current_idx, label_visibility="collapsed"
    )
    chosen_key = page_keys[page_labels.index(chosen_label)]
    if chosen_key != st.session_state["active_page"]:
        st.session_state["active_page"] = chosen_key
        st.rerun()

    st.divider()
    st.markdown("#### Pengaturan Tampilan")
    is_moon = st.toggle("Mode Gelap (Moon)", value=(st.session_state["app_theme"] == "moon"))
    new_mode = "moon" if is_moon else "light"
    if new_mode != st.session_state["app_theme"]:
        st.session_state["app_theme"] = new_mode
        st.rerun()

    st.divider()
    st.markdown("#### Filter Data")
    df_raw = load_data()

    # Filter Tahun Anggaran berdasarkan tanggal mulai efektif
    years_available = sorted(list(set([d.year for d in df_raw["_TGL_EFEKTIF"].dropna() if hasattr(d, "year")])))
    if years_available:
        f_tahun = st.selectbox("Tahun Anggaran", ["Semua"] + [str(y) for y in years_available])
    else:
        f_tahun = "Semua"

    bidang_options = ["Semua"] + sorted([b for b in df_raw["BIDANG"].dropna().unique() if str(b).strip()])
    f_bidang = st.selectbox("Bidang", bidang_options)

    # Filter berjenjang: opsi Program & Lokasi menyempit mengikuti Bidang yang dipilih
    df_scoped = df_raw if f_bidang == "Semua" else df_raw[df_raw["BIDANG"] == f_bidang]

    program_options = ["Semua"] + sorted(
        [p for p in df_scoped["PROGRAM PELATIHAN"].dropna().unique() if str(p).strip()]
    )
    f_program = st.selectbox("Program Pelatihan", program_options)

    df_scoped2 = df_scoped if f_program == "Semua" else df_scoped[df_scoped["PROGRAM PELATIHAN"] == f_program]

    lokasi_options = ["Semua"] + sorted([l for l in df_scoped2["LOKASI"].dropna().unique() if str(l).strip()])
    f_lokasi = st.selectbox("Lokasi", lokasi_options)

    f_status = st.radio("Status Checklist", ["Semua", "Selesai", "Belum Selesai"], horizontal=True)

    if st.button("Muat ulang data", width="stretch", icon=":material/refresh:"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("#### Hak Akses")
    if not st.session_state.get("is_admin", False):
        with st.expander("Masuk sebagai Admin", expanded=False):
            st.caption("Masuk untuk menambah, mengedit, atau menghapus data pelatihan.")
            pin_input = st.text_input("PIN Admin", type="password", key="admin_pin_sidebar", help="PIN default: bpvp2026")
            if st.button("Masuk Admin", width="stretch", icon=":material/login:"):
                expected_pin = str(get_config("admin_pin"))
                if str(pin_input).strip() == expected_pin:
                    st.session_state["is_admin"] = True
                    st.toast("Mode Admin berhasil diaktifkan!", icon=":material/lock_open:")
                    st.rerun()
                else:
                    st.error("PIN Admin salah.")
    else:
        st.success("✅ **Mode Admin Aktif**")
        st.caption("Anda memiliki akses penuh untuk menambah, mengedit, dan menghapus data.")
        if st.button("Keluar Admin", width="stretch", icon=":material/logout:"):
            st.session_state["is_admin"] = False
            st.toast("Mode Admin dinonaktifkan.", icon=":material/lock:")
            st.rerun()

# ============================================================
# Penerapan Filter
# ============================================================
df = df_raw.copy()
if f_tahun != "Semua":
    df = df[df["_TGL_EFEKTIF"].apply(lambda d: d is not None and hasattr(d, "year") and str(d.year) == f_tahun)]
if f_bidang != "Semua":
    df = df[df["BIDANG"] == f_bidang]
if f_program != "Semua":
    df = df[df["PROGRAM PELATIHAN"] == f_program]
if f_lokasi != "Semua":
    df = df[df["LOKASI"] == f_lokasi]
if f_status == "Selesai":
    df = df[df["CHECK"]]
elif f_status == "Belum Selesai":
    df = df[~df["CHECK"]]

# ============================================================
# Header
# ============================================================
st.markdown(
    f"""<div class="app-header">
        <h1>Monitoring Program Pelatihan Vokasi</h1>
        <div class="app-header-tag">BPVP KENDARI</div>
    </div>""",
    unsafe_allow_html=True,
)

active_page = st.session_state["active_page"]

# ============================================================
# HALAMAN: DASHBOARD
# ============================================================
if active_page == "dashboard":
    render_dashboard(df, c_theme)

# ============================================================
# HALAMAN: LIHAT DATA
# ============================================================
elif active_page == "lihat":
    c_caption, c_excel = st.columns([3, 1.2])
    with c_caption:
        st.caption(f"Menampilkan {len(df)} dari {len(df_raw)} baris data.")
    with c_excel:
        if not df.empty:
            excel_bytes = export_monitoring_excel(df, kapasitas_default=get_config("kapasitas_default"))
            st.download_button(
                label="Unduh Rekap Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"Rekap_Pelatihan_BPVP_Kendari_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                icon=":material/download:",
                width="stretch",
            )

    if df.empty:
        st.info("Tidak ada data yang cocok dengan filter yang dipilih. Coba ubah atau reset filter di sidebar.")
    else:
        st.markdown(render_data_table_html(df, c_theme), unsafe_allow_html=True)

        st.divider()
        st.markdown("**Aksi Cepat Baris Data**")
        valid_no = [str(int(float(v))) for v in df["NO"].dropna() if str(v).replace(".", "", 1).isdigit()]
        sel_no = st.selectbox("Pilih NO baris untuk aksi cepat / edit / hapus", ["-"] + valid_no)

        is_admin = st.session_state.get("is_admin", False)

        if sel_no != "-":
            target_no = int(sel_no)
            row_match = df_raw[df_raw["NO"] == target_no]
            is_cur_done = bool(row_match.iloc[0]["CHECK"]) if not row_match.empty else False
            nama = row_match.iloc[0]["PROGRAM PELATIHAN"] if not row_match.empty else "(tidak diketahui)"

            toggle_text = "Tandai Belum Selesai" if is_cur_done else "Tandai Selesai (CHECK)"
            toggle_icon = ":material/cancel:" if is_cur_done else ":material/check_circle:"

            ac1, ac2, ac3 = st.columns([1.3, 1, 1])
            with ac1:
                if st.button(toggle_text, width="stretch", icon=toggle_icon, disabled=not is_admin):
                    with st.spinner("Memperbarui status..."):
                        if toggle_check_row(target_no):
                            st.toast(f"Status NO {target_no} ({nama}) berhasil diubah!", icon=":material/check:")
                            st.rerun()
            with ac2:
                if st.button("Edit baris ini", width="stretch", icon=":material/edit:", disabled=not is_admin):
                    st.session_state["edit_no"] = target_no
                    go_to("edit")
                    st.rerun()
            with ac3:
                if st.button("Hapus baris ini", width="stretch", icon=":material/delete:", disabled=not is_admin):
                    st.session_state["confirm_delete_no"] = target_no

            if not is_admin:
                st.caption("🔒 *Fitur ubah status, edit, dan hapus memerlukan otentikasi Admin di sidebar.*")
        else:
            st.caption("Pilih salah satu nomor baris pada pemilih di atas untuk mengubah status, mengedit, atau menghapus.")

        if st.session_state.get("confirm_delete_no") is not None:
            no_target = st.session_state["confirm_delete_no"]
            row_match = df_raw[df_raw["NO"] == no_target]
            nama = row_match.iloc[0]["PROGRAM PELATIHAN"] if not row_match.empty else "(tidak diketahui)"
            confirm_delete_dialog(no_target, nama)

# ============================================================
# HALAMAN: TAMBAH / EDIT DATA
# ============================================================
elif active_page == "edit":
    is_admin = st.session_state.get("is_admin", False)
    if not is_admin:
        st.warning("Halaman ini memerlukan hak akses Admin untuk menambah atau mengubah data pelatihan.")
        with st.container(border=True):
            st.markdown("#### Masuk sebagai Admin")
            st.caption("Masukkan PIN Admin untuk membuka form tambah atau edit data pelatihan.")
            pin_form = st.text_input("PIN Admin", type="password", key="admin_pin_page_unlock", help="PIN default: bpvp2026")
            if st.button("Buka Akses Admin", type="primary", width="stretch", icon=":material/lock_open:"):
                expected_pin = str(get_config("admin_pin"))
                if str(pin_form).strip() == expected_pin:
                    st.session_state["is_admin"] = True
                    st.toast("Mode Admin berhasil diaktifkan!", icon=":material/verified_user:")
                    st.rerun()
                else:
                    st.error("PIN Admin salah. Silakan coba kembali.")
    else:
        df_all = load_data()
        edit_no = st.session_state.get("edit_no")
        editing_row = None
        if edit_no is not None:
            match = df_all[df_all["NO"] == edit_no]
            if not match.empty:
                editing_row = match.iloc[0]
            else:
                st.warning("Baris yang ingin diedit tidak ditemukan (mungkin sudah dihapus). Menampilkan form tambah baru.")
                st.session_state["edit_no"] = None

        st.subheader("Edit Data Pelatihan" if editing_row is not None else "Tambah Program Pelatihan Baru")
        tag = str(edit_no) if edit_no is not None else "new"

    with st.form("form_edit"):
        c1, c2, c3, c4 = st.columns([1.5, 2, 1.5, 1])
        b_list = sorted([str(x).strip() for x in df_all["BIDANG"].dropna().unique() if str(x).strip()])

        with c1:
            allow_new_bidang = st.checkbox("Bidang baru?", value=False, key=f"chk_new_bidang_{tag}", help="Centang jika bidang belum ada di daftar")
            if allow_new_bidang or not b_list:
                form_bidang = st.text_input(
                    "Bidang*", value=editing_row["BIDANG"] if editing_row is not None else "", key=f"in_bidang_text_{tag}"
                )
            else:
                default_idx = (
                    b_list.index(editing_row["BIDANG"])
                    if editing_row is not None and editing_row["BIDANG"] in b_list
                    else 0
                )
                form_bidang = st.selectbox("Bidang*", b_list, index=default_idx, key=f"in_bidang_sel_{tag}")
        with c2:
            form_prog = st.text_input(
                "Program Pelatihan*", value=editing_row["PROGRAM PELATIHAN"] if editing_row is not None else "", key=f"in_prog_{tag}"
            )
        with c3:
            form_lok = st.text_input(
                "Lokasi", value=editing_row["LOKASI"] if editing_row is not None else "BPVP Kendari", key=f"in_lok_{tag}"
            )
        with c4:
            form_pst = st.number_input(
                "Peserta Terisi",
                min_value=0,
                step=1,
                value=int(editing_row["PESERTA"]) if editing_row is not None else 0,
                key=f"in_pst_{tag}",
            )

        kapasitas = get_config("kapasitas_default")
        if form_pst > kapasitas:
            st.caption(f":material/warning: Peserta melebihi kapasitas standar ({kapasitas} orang/paket).")

        form_check = st.checkbox(
            "Sudah Selesai (CHECK)", value=bool(editing_row["CHECK"]) if editing_row is not None else False, key=f"in_check_{tag}"
        )

        st.caption("Isi minimal salah satu pasangan tanggal (Aktual atau Rencana) agar program muncul di grafik jadwal & peringatan H-10. Format: Tanggal/Bulan/Tahun.")
        d1, d2, d3, d4 = st.columns(4)
        t_mulai = d1.date_input(
            "Tgl Mulai (Aktual)",
            value=parse_date(editing_row.get("TANGGAL MULAI")) if editing_row is not None else None,
            format="DD/MM/YYYY",
            key=f"in_tm_{tag}",
        )
        t_selesai = d2.date_input(
            "Tgl Selesai (Aktual)",
            value=parse_date(editing_row.get("TANGGAL SELESAI")) if editing_row is not None else None,
            format="DD/MM/YYYY",
            key=f"in_ts_{tag}",
        )
        r_mulai = d3.date_input(
            "Rencana Mulai",
            value=parse_date(editing_row.get("RENCANA MULAI")) if editing_row is not None else None,
            format="DD/MM/YYYY",
            key=f"in_rm_{tag}",
        )
        r_selesai = d4.date_input(
            "Rencana Selesai",
            value=parse_date(editing_row.get("RENCANA SELESAI")) if editing_row is not None else None,
            format="DD/MM/YYYY",
            key=f"in_rs_{tag}",
        )
        ket = st.text_area("Keterangan", value=editing_row["KETERANGAN"] if editing_row is not None else "", height=80, key=f"in_ket_{tag}")

        b_cancel, b_save, _ = st.columns([1, 1, 4])
        cancel_clicked = b_cancel.form_submit_button("Batal", width="stretch")
        save_clicked = b_save.form_submit_button("Simpan Data", width="stretch", type="primary")

    if cancel_clicked:
        st.session_state.pop("edit_no", None)
        go_to("lihat")
        st.rerun()

    if save_clicked:
        errors = []
        if not form_prog.strip():
            errors.append("Program Pelatihan wajib diisi.")
        if not str(form_bidang).strip():
            errors.append("Bidang wajib diisi.")
        if not any([t_mulai, t_selesai, r_mulai, r_selesai]):
            errors.append("Minimal isi satu pasang tanggal (Aktual atau Rencana).")
        if t_mulai and t_selesai and t_selesai < t_mulai:
            errors.append("Tanggal Selesai (Aktual) tidak boleh lebih awal dari Tanggal Mulai (Aktual).")
        if r_mulai and r_selesai and r_selesai < r_mulai:
            errors.append("Rencana Selesai tidak boleh lebih awal dari Rencana Mulai.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            # Ambil data terbaru langsung dari Sheets (bukan cache) untuk kurangi
            # risiko menimpa perubahan orang lain & menentukan NO baru yang akurat.
            df_fresh = load_data_fresh()
            no_val = (
                int(editing_row["NO"])
                if editing_row is not None
                else int(pd.to_numeric(df_fresh["NO"], errors="coerce").fillna(0).max() + 1)
            )
            new_data = {
                "NO": no_val,
                "BIDANG": str(form_bidang).strip(),
                "PROGRAM PELATIHAN": form_prog.strip(),
                "CHECK": form_check,
                "PESERTA": int(form_pst),
                "LOKASI": form_lok.strip(),
                "TANGGAL MULAI": format_date(t_mulai),
                "TANGGAL SELESAI": format_date(t_selesai),
                "RENCANA MULAI": format_date(r_mulai),
                "RENCANA SELESAI": format_date(r_selesai),
                "KETERANGAN": ket.strip(),
            }

            with st.spinner("Menyimpan data..."):
                if editing_row is not None:
                    success = update_row(no_val, new_data)
                else:
                    success = add_row(new_data)

            if success:
                st.session_state.pop("edit_no", None)
                st.toast("Data berhasil disimpan.", icon=":material/check_circle:")
                go_to("lihat")
                st.rerun()