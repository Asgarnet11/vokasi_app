import streamlit as st

# Palet terinspirasi suasana bengkel/workshop vokasi — bukan dashboard tech
# generik. Terang = kertas & kayu bengkel; Gelap = ruang produksi malam hari
# dengan lampu sorot amber.
THEME_TOKENS = {
    "light": {
        "bg_app": "#FAF7F1",       # kertas hangat, bukan putih dingin
        "bg_surface": "#FFFFFF",
        "bg_sidebar": "#F1EAD9",   # kayu muda
        "border": "#E3D9C4",
        "text_primary": "#241E15",
        "text_secondary": "#7A6F5B",
        "accent": "#C0742F",       # ochre / amber bengkel
        "accent_soft": "#F1DCC0",
        "success": "#2F7A63",      # teal tua — "selesai"
        "warning": "#B23B2E",      # merah bata — peringatan
        "grid": "#E3D9C4",
    },
    "moon": {
        "bg_app": "#171310",       # charcoal hangat, bukan navy
        "bg_surface": "#201A14",
        "bg_sidebar": "#120E0B",
        "border": "#362B1E",
        "text_primary": "#F5EEE1",
        "text_secondary": "#A6997E",
        "accent": "#E0913F",       # lampu sorot bengkel
        "accent_soft": "#3A2A17",
        "success": "#4FA98A",
        "warning": "#E2685A",
        "grid": "#362B1E",
    },
}


def apply_theme(mode: str):
    c = THEME_TOKENS.get(mode, THEME_TOKENS["moon"])
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, .stApp {{
            font-family: 'Inter', sans-serif !important;
            background-color: {c["bg_app"]} !important;
            color: {c["text_primary"]} !important;
        }}
        /* Sembunyikan menu bawaan (hamburger "Deploy"/GitHub) & footer saja.
           JANGAN sembunyikan seluruh header/toolbar — tombol buka/tutup
           sidebar ("collapsedControl" / "stSidebarCollapseButton") hidup di
           dalam header, sehingga kalau header disembunyikan total, sidebar
           jadi tidak bisa dibuka sama sekali. */
        footer {{ visibility: hidden; }}
        header {{ background: transparent !important; }}
        #MainMenu {{ visibility: hidden; }}

        /* Pastikan tombol sidebar tetap terlihat & berwarna sesuai tema */
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="collapsedControl"] button,
        [data-testid="collapsedControl"] svg,
        [data-testid="stSidebarCollapseButton"] svg {{
            visibility: visible !important;
            display: flex !important;
            opacity: 1 !important;
            color: {c["text_primary"]} !important;
            fill: {c["text_primary"]} !important;
        }}
        .block-container {{ padding-top: 1.5rem !important; max-width: 1240px !important; }}

        /* Header aplikasi — aksen sebagai garis tipis di kiri, bukan blok warna penuh */
        .app-header {{
            background: {c["bg_surface"]};
            padding: 18px 24px;
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 20px;
            border: 1px solid {c["border"]};
            border-left: 3px solid {c["accent"]};
        }}
        .app-header h1 {{
            font-size: 21px !important; font-weight: 700 !important;
            letter-spacing: -0.01em;
            margin: 0 !important; color: {c["text_primary"]} !important;
        }}
        .app-header .app-header-tag {{
            font-weight: 600; color: {c["accent"]}; font-size: 13px;
            letter-spacing: 0.02em;
        }}

        section[data-testid="stSidebar"] {{
            background-color: {c["bg_sidebar"]} !important;
            border-right: 1px solid {c["border"]} !important;
        }}
        section[data-testid="stSidebar"] * {{ color: {c["text_primary"]} !important; }}

        /* ============================================================
           NAVIGASI SIDEBAR — ubah st.radio bawaan (bulatan + label polos)
           jadi pill/segmented button yang selaras tema, bukan widget
           default Streamlit yang kelihatan generik.
           ============================================================ */
        .nav-pills [role="radiogroup"] {{
            gap: 6px !important;
        }}
        .nav-pills label[data-baseweb="radio"] {{
            background-color: {c["bg_surface"]} !important;
            border: 1px solid {c["border"]} !important;
            border-radius: 8px !important;
            padding: 10px 14px !important;
            margin-bottom: 0 !important;
            cursor: pointer;
            transition: background-color .15s ease, border-color .15s ease;
        }}
        .nav-pills label[data-baseweb="radio"]:hover {{
            border-color: {c["accent"]} !important;
        }}
        /* Sembunyikan bulatan radio asli — bentuknya sudah jadi pill utuh */
        .nav-pills label[data-baseweb="radio"] > div:first-child {{
            display: none !important;
        }}
        .nav-pills label[data-baseweb="radio"] div[data-testid="stMarkdownContainer"] p {{
            font-weight: 600 !important;
            font-size: 14px !important;
            margin: 0 !important;
        }}
        /* State terpilih — isi solid warna aksen, teks putih */
        .nav-pills label[data-baseweb="radio"]:has(input:checked) {{
            background-color: {c["accent"]} !important;
            border-color: {c["accent"]} !important;
        }}
        .nav-pills label[data-baseweb="radio"]:has(input:checked) * {{
            color: #FFFFFF !important;
        }}

        /* ============================================================
           WIDGET NATIVE — sebelumnya cuma selectbox yang diwarnai di
           sini, sehingga text_input / number_input / date_input /
           text_area tetap ikut tema default Streamlit (biasanya gelap
           kalau OS/browser pengguna dark mode) walau app_theme = light.
           Selector di bawah ini menyamakan SEMUA kotak input.
           ============================================================ */
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"],
        div[data-baseweb="textarea"],
        div[data-baseweb="base-input"],
        div[data-baseweb="datepicker"] > div,
        div[data-baseweb="popover"] div[role="listbox"] {{
            background-color: {c["bg_surface"]} !important;
            border-color: {c["border"]} !important;
            color: {c["text_primary"]} !important;
        }}
        div[data-baseweb="select"] span,
        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea,
        div[data-baseweb="base-input"] input,
        div[data-baseweb="datepicker"] input {{
            color: {c["text_primary"]} !important;
            background-color: transparent !important;
        }}
        /* Opsi dropdown (selectbox terbuka, kalender date_input) */
        ul[role="listbox"] li,
        div[data-baseweb="calendar"],
        div[data-baseweb="calendar"] * {{
            background-color: {c["bg_surface"]} !important;
            color: {c["text_primary"]} !important;
        }}
        ul[role="listbox"] li:hover {{
            background-color: {c["accent_soft"]} !important;
        }}
        /* Stepper +/- pada number_input */
        [data-testid="stNumberInputStepUp"],
        [data-testid="stNumberInputStepDown"] {{
            background-color: {c["bg_surface"]} !important;
            color: {c["text_primary"]} !important;
            border-color: {c["border"]} !important;
        }}
        /* Checkbox & radio label */
        [data-testid="stCheckbox"] label p,
        [data-testid="stRadio"] label p {{
            color: {c["text_primary"]} !important;
        }}

        /* Card: satu level shadow konsisten, bukan default flat sama rata */
        [data-testid="stVerticalBlockBorderWrapper"] > div {{
            background-color: {c["bg_surface"]} !important;
            border-color: {c["border"]} !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.06);
        }}

        .stButton > button {{
            background-color: {c["bg_surface"]} !important;
            color: {c["text_primary"]} !important;
            border: 1px solid {c["border"]} !important;
            border-radius: 6px !important;
        }}
        .stButton > button:hover {{
            border-color: {c["accent"]} !important;
            color: {c["accent"]} !important;
        }}
        button[kind="primary"] {{
            background-color: {c["accent"]} !important;
            border-color: {c["accent"]} !important;
            color: #FFFFFF !important;
        }}

        [data-testid="stMetricValue"] {{ color: {c["text_primary"]} !important; }}
        [data-testid="stMetricLabel"] {{ color: {c["text_secondary"]} !important; }}

        .stProgress > div > div > div > div {{ background-color: {c["accent"]} !important; }}

        hr {{ border-color: {c["border"]} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return c