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

        div[data-baseweb="select"] > div {{
            background-color: {c["bg_surface"]} !important;
            border-color: {c["border"]} !important;
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

        /* ============================================================
           WIDGET FORM — sebelumnya tidak ditema sama sekali sehingga
           tetap memakai warna gelap bawaan Streamlit (terlihat "nyasar"
           saat aplikasi dalam mode terang). Sekarang semua disamakan
           dengan c_theme.
           ============================================================ */

        /* Label semua widget (Program Pelatihan*, Lokasi, dst) —
           sebelumnya kontrasnya terlalu rendah/pudar */
        label, div[data-testid="stWidgetLabel"] p, div[data-testid="stWidgetLabel"] label {{
            color: {c["text_primary"]} !important;
            font-weight: 500 !important;
            opacity: 1 !important;
        }}

        /* Text input, number input, text area, date input */
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        .stDateInput input {{
            background-color: {c["bg_surface"]} !important;
            color: {c["text_primary"]} !important;
            border: 1px solid {c["border"]} !important;
            border-radius: 6px !important;
        }}
        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus,
        .stDateInput input:focus {{
            border-color: {c["accent"]} !important;
            box-shadow: 0 0 0 1px {c["accent"]} !important;
        }}
        .stTextInput input::placeholder,
        .stNumberInput input::placeholder,
        .stTextArea textarea::placeholder {{
            color: {c["text_secondary"]} !important;
            opacity: 0.8;
        }}

        /* Tombol +/- pada number_input */
        .stNumberInput button {{
            background-color: {c["bg_surface"]} !important;
            border: 1px solid {c["border"]} !important;
            color: {c["text_primary"]} !important;
        }}
        .stNumberInput button:hover {{
            border-color: {c["accent"]} !important;
            color: {c["accent"]} !important;
        }}

        /* Checkbox (BaseWeb) — sebelumnya kotak hitam solid, sulit
           dibedakan checked/unchecked */
        div[data-baseweb="checkbox"] > div:first-child {{
            background-color: {c["bg_surface"]} !important;
            border: 1.5px solid {c["border"]} !important;
        }}
        div[data-baseweb="checkbox"] input:checked ~ div {{
            background-color: {c["accent"]} !important;
            border-color: {c["accent"]} !important;
        }}
        .stCheckbox label p {{ color: {c["text_primary"]} !important; }}

        /* Radio (navigasi sidebar & filter status) — sebelumnya bulatan
           merah bawaan Streamlit, tidak mengikuti aksen tema */
        div[data-baseweb="radio"] > label > div:first-child {{
            border-color: {c["text_secondary"]} !important;
        }}
        div[data-baseweb="radio"] input:checked + div {{
            border-color: {c["accent"]} !important;
        }}
        div[data-baseweb="radio"] input:checked + div > div {{
            background-color: {c["accent"]} !important;
        }}
        .stRadio label p {{ color: {c["text_primary"]} !important; }}

        /* Toggle (mode gelap) */
        div[data-baseweb="checkbox"][aria-checked] {{ accent-color: {c["accent"]}; }}
        .stToggle [data-baseweb="checkbox"] div[aria-checked="true"] {{
            background-color: {c["accent"]} !important;
        }}

        /* Kalender popover date_input */
        div[data-baseweb="calendar"] {{
            background-color: {c["bg_surface"]} !important;
            color: {c["text_primary"]} !important;
        }}
        div[data-baseweb="calendar"] button {{ color: {c["text_primary"]} !important; }}

        /* Tombol "Batal" (secondary) — pastikan teks tetap kontras */
        button[kind="secondary"] p {{ color: {c["text_primary"]} !important; }}
        button[kind="primary"] p {{ color: #FFFFFF !important; }}

        /* Caption / helper text */
        .stCaption, [data-testid="stCaptionContainer"] p {{
            color: {c["text_secondary"]} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return c