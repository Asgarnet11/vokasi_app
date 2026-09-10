"""
Tabel data custom berbasis HTML.

st.dataframe bawaan Streamlit dirender lewat komponen internal (grid khusus)
yang tidak bisa di-restyle penuh lewat CSS biasa — makanya sebelumnya tabel
tetap tampil gelap meski aplikasi sedang dalam mode terang. Modul ini
menggantinya dengan tabel HTML polos yang seluruh warnanya diambil dari
c_theme, sehingga selalu konsisten dengan tema aktif (light/moon).
"""
import html
import pandas as pd

# Kolom yang ditampilkan di tabel, berikut label header & alignment-nya.
_TABLE_COLUMNS = [
    ("NO", "NO", "left", 56),
    ("BIDANG", "Bidang", "left", 150),
    ("PROGRAM PELATIHAN", "Program Pelatihan", "left", 220),
    ("CHECK", "Selesai?", "center", 90),
    ("PESERTA", "Peserta", "right", 80),
    ("LOKASI", "Lokasi", "left", 140),
    ("TANGGAL MULAI", "Tgl Mulai", "left", 110),
    ("TANGGAL SELESAI", "Tgl Selesai", "left", 110),
    ("RENCANA MULAI", "Rencana Mulai", "left", 110),
    ("RENCANA SELESAI", "Rencana Selesai", "left", 120),
    ("KETERANGAN", "Keterangan", "left", 220),
]


def _esc(value) -> str:
    """Escape nilai jadi string HTML aman (cegah injeksi / rendering rusak)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return html.escape(str(value))


def _check_badge(is_done: bool, c_theme: dict) -> str:
    if is_done:
        return (
            f'<span style="display:inline-flex;align-items:center;justify-content:center;'
            f'width:22px;height:22px;border-radius:6px;background:{c_theme["success"]};'
            f'color:#FFFFFF;font-size:13px;font-weight:700;">&#10003;</span>'
        )
    return (
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:22px;height:22px;border-radius:6px;border:1.5px solid {c_theme["border"]};">'
        f"</span>"
    )


def render_data_table_html(df: pd.DataFrame, c_theme: dict, max_height: int = 560) -> str:
    """Bangun string HTML tabel data yang sepenuhnya mengikuti c_theme."""
    header_cells = "".join(
        f'<th style="text-align:{align};min-width:{width}px;padding:10px 14px;'
        f'position:sticky;top:0;background:{c_theme["bg_surface"]};'
        f'border-bottom:2px solid {c_theme["border"]};color:{c_theme["text_secondary"]};'
        f'font-size:11.5px;font-weight:700;letter-spacing:0.03em;text-transform:uppercase;'
        f'white-space:nowrap;z-index:1;">{_esc(label)}</th>'
        for _, label, align, width in _TABLE_COLUMNS
    )

    body_rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        row_bg = c_theme["bg_surface"] if i % 2 == 0 else c_theme["bg_app"]
        cells = []
        for col, _, align, width in _TABLE_COLUMNS:
            if col == "CHECK":
                content = _check_badge(bool(row.get("CHECK", False)), c_theme)
            elif col == "PESERTA":
                try:
                    content = f'{int(row.get("PESERTA", 0)):,}'.replace(",", ".")
                except (TypeError, ValueError):
                    content = "0"
            elif col == "NO":
                try:
                    content = str(int(float(row.get("NO"))))
                except (TypeError, ValueError):
                    content = ""
            else:
                content = _esc(row.get(col, ""))
                if not content:
                    content = f'<span style="color:{c_theme["border"]};">&mdash;</span>'
            cells.append(
                f'<td title="{_esc(row.get(col, ""))}" style="text-align:{align};'
                f'min-width:{width}px;padding:9px 14px;white-space:nowrap;'
                f'overflow:hidden;text-overflow:ellipsis;max-width:260px;'
                f'border-bottom:1px solid {c_theme["border"]};color:{c_theme["text_primary"]};'
                f'font-size:13px;">{content}</td>'
            )
        body_rows.append(
            f'<tr style="background:{row_bg};" '
            f'onmouseover="this.style.background=\'{c_theme["accent_soft"]}\'" '
            f'onmouseout="this.style.background=\'{row_bg}\'">{"".join(cells)}</tr>'
        )

    html_out = f"""
    <div style="max-height:{max_height}px; overflow:auto; border:1px solid {c_theme['border']};
                border-radius:10px; background:{c_theme['bg_surface']};">
        <table style="border-collapse:collapse; width:100%; font-family:'Inter',sans-serif;">
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{''.join(body_rows) if body_rows else ''}</tbody>
        </table>
    </div>
    """
    # Hilangkan leading whitespace tiap baris — kalau tidak, st.markdown() bisa
    # salah mengenali blok ini sebagai indented code block (lihat bug kartu
    # donut di dashboard_view.py) dan menampilkan tag HTML mentah, bukan tabel.
    return "\n".join(line.strip() for line in html_out.strip().splitlines())