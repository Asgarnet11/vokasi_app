import streamlit as st
import pandas as pd
from datetime import datetime, date
from services.gsheets import load_data, save_data, COLUMNS
from components.theme import apply_theme
from components.dashboard_view import render_dashboard

# Konfigurasi Halaman & Tema
st.set_page_config(page_title="Monitoring Program Pelatihan Vokasi", page_icon=":material/monitoring:", layout="wide")
if "app_theme" not in st.session_state:
    st.session_state["app_theme"] = "moon"
c_theme = apply_theme(st.session_state["app_theme"])

# Sidebar: Tema & Filter
with st.sidebar:
    st.markdown("#### Pengaturan Tampilan")
    is_moon = st.toggle("🌙 Mode Gelap (Moon)", value=(st.session_state["app_theme"] == "moon"))
    new_mode = "moon" if is_moon else "light"
    if new_mode != st.session_state["app_theme"]:
        st.session_state["app_theme"] = new_mode
        st.rerun()

    st.divider()
    st.markdown("#### Filter Data")
    df_raw = load_data()

    f_bidang = st.selectbox("Bidang", ["Semua"] + sorted([b for b in df_raw["BIDANG"].dropna().unique() if str(b).strip()]))
    f_program = st.selectbox("Program Pelatihan", ["Semua"] + sorted([p for p in df_raw["PROGRAM PELATIHAN"].dropna().unique() if str(p).strip()]))
    f_lokasi = st.selectbox("Lokasi", ["Semua"] + sorted([l for l in df_raw["LOKASI"].dropna().unique() if str(l).strip()]))
    f_status = st.radio("Status Checklist", ["Semua", "Selesai", "Belum Selesai"], horizontal=True)

    if st.button("Muat ulang data", width='stretch'):
        st.cache_data.clear()
        st.rerun()

# Penerapan Filter
df = df_raw.copy()
if f_bidang != "Semua": df = df[df["BIDANG"] == f_bidang]
if f_program != "Semua": df = df[df["PROGRAM PELATIHAN"] == f_program]
if f_lokasi != "Semua": df = df[df["LOKASI"] == f_lokasi]
if f_status == "Selesai": df = df[df["CHECK"]]
elif f_status == "Belum Selesai": df = df[~df["CHECK"]]

# Header Dashboard
st.markdown(
    f"""<div class="app-header">
        <h1>Monitoring Program Pelatihan Vokasi</h1>
        <div class="app-header-tag">BPVP KENDARI</div>
    </div>""",
    unsafe_allow_html=True,
)

tab_dash, tab_lihat, tab_edit = st.tabs(["📊 Dashboard", "📋 Lihat Data", "✏️ Edit Data"])

# TAB 1: DASHBOARD
with tab_dash:
    render_dashboard(df, c_theme)

# TAB 2: LIHAT DATA
with tab_lihat:
    st.caption(f"Menampilkan {len(df)} dari {len(df_raw)} baris data.")
    st.dataframe(df.drop(columns=["_TGL_EFEKTIF"], errors="ignore"), width='stretch', hide_index=True)

    st.divider()
    st.markdown("**Aksi Cepat Baris**")
    valid_no = [str(int(float(v))) for v in df["NO"].dropna() if str(v).replace('.','',1).isdigit()]
    sel_no = st.selectbox("Pilih NO baris untuk diedit / dihapus", ["-"] + valid_no)
    ac1, ac2 = st.columns(2)

    with ac1:
        if st.button("✏️ Edit baris ini", width='stretch', disabled=(sel_no == "-")):
            st.session_state["edit_no"] = int(sel_no)
            st.info("Baris dimuat. Silakan buka tab **Edit Data**.")
    with ac2:
        if st.button("🗑️ Hapus baris ini", width='stretch', disabled=(sel_no == "-")):
            df_all = load_data()
            save_data(df_all[df_all["NO"] != int(sel_no)])
            st.success(f"Baris NO {sel_no} berhasil dihapus.")
            st.rerun()

# TAB 3: EDIT DATA
with tab_edit:
    df_all = load_data()
    edit_no = st.session_state.get("edit_no", None)
    editing_row = df_all[df_all["NO"] == edit_no].iloc[0] if (edit_no is not None and not df_all[df_all["NO"] == edit_no].empty) else None

    st.subheader("Edit Data Pelatihan" if editing_row is not None else "Tambah Program Pelatihan Baru")
    with st.form("form_edit"):
        c1, c2, c3, c4 = st.columns([1.5, 2, 1.5, 1])
        b_list = sorted([str(x).strip() for x in df_all["BIDANG"].dropna().unique() if str(x).strip()])
        with c1: form_bidang = st.selectbox("Bidang", b_list, index=b_list.index(editing_row["BIDANG"]) if editing_row is not None and editing_row["BIDANG"] in b_list else 0)
        with c2: form_prog = st.text_input("Program Pelatihan*", value=editing_row["PROGRAM PELATIHAN"] if editing_row is not None else "")
        with c3: form_lok = st.text_input("Lokasi", value=editing_row["LOKASI"] if editing_row is not None else "BPVP Kendari")
        with c4: form_pst = st.number_input("Peserta Terisi", min_value=0, step=1, value=int(editing_row["PESERTA"]) if editing_row is not None else 0)

        form_check = st.checkbox("Sudah Selesai (CHECK)", value=bool(editing_row["CHECK"]) if editing_row is not None else False)

        def to_d(val):
            for fmt in ["%d %b %Y", "%Y-%m-%d", "%d/%m/%Y"]:
                try: return datetime.strptime(str(val).strip(), fmt).date()
                except: pass
            return None

        d1, d2, d3, d4 = st.columns(4)
        t_mulai = d1.date_input("Tgl Mulai", value=to_d(editing_row.get("TANGGAL MULAI")) if editing_row is not None else None)
        t_selesai = d2.date_input("Tgl Selesai", value=to_d(editing_row.get("TANGGAL SELESAI")) if editing_row is not None else None)
        r_mulai = d3.date_input("Rencana Mulai", value=to_d(editing_row.get("RENCANA MULAI")) if editing_row is not None else None)
        r_selesai = d4.date_input("Rencana Selesai", value=to_d(editing_row.get("RENCANA SELESAI")) if editing_row is not None else None)
        ket = st.text_area("Keterangan", value=editing_row["KETERANGAN"] if editing_row is not None else "", height=80)

        b_cancel, b_save, _ = st.columns([1, 1, 4])
        if b_cancel.form_submit_button("Batal", width='stretch'):
            st.session_state.pop("edit_no", None)
            st.rerun()
        if b_save.form_submit_button("Simpan Data", width='stretch', type="primary"):
            if not form_prog.strip():
                st.error("Program Pelatihan wajib diisi.")
            else:
                fmt_d = lambda d: d.strftime("%d %b %Y") if isinstance(d, (datetime, date)) else ""
                no_val = int(editing_row["NO"]) if editing_row is not None else int(pd.to_numeric(df_all["NO"], errors="coerce").fillna(0).max() + 1)
                new_data = {
                    "NO": no_val, "BIDANG": form_bidang, "PROGRAM PELATIHAN": form_prog.strip(),
                    "CHECK": form_check, "PESERTA": int(form_pst), "LOKASI": form_lok.strip(),
                    "TANGGAL MULAI": fmt_d(t_mulai), "TANGGAL SELESAI": fmt_d(t_selesai),
                    "RENCANA MULAI": fmt_d(r_mulai), "RENCANA SELESAI": fmt_d(r_selesai), "KETERANGAN": ket.strip()
                }
                if editing_row is not None:
                    df_all.loc[df_all["NO"] == editing_row["NO"], COLUMNS] = [new_data[c] for c in COLUMNS]
                else:
                    df_all = pd.concat([df_all, pd.DataFrame([new_data])], ignore_index=True)
                save_data(df_all)
                st.session_state.pop("edit_no", None)
                st.success("Data berhasil disimpan.")
                st.rerun()