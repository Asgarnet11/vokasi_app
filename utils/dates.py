"""
Utilitas parsing & formatting tanggal terpusat.

Sebelumnya logic parsing tanggal terduplikasi di 3 tempat berbeda
(gsheets.py: parse_tgl_mulai & parse_tgl_selesai, app.py: to_d) dengan
daftar format yang tidak konsisten. Modul ini menyatukan semuanya
supaya cukup diubah/diperbaiki di satu tempat.
"""
from datetime import datetime, date

# Semua format tanggal yang mungkin muncul di Google Sheets.
DATE_FORMATS = ["%d %b %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]


def parse_date(value) -> date | None:
    """Parse string tanggal ke objek date, coba semua format yang didukung.
    Mengembalikan None jika kosong atau tidak ada format yang cocok."""
    val = str(value).strip() if value is not None else ""
    if not val:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


def parse_date_from_columns(row, columns: list[str]) -> date | None:
    """Coba parse tanggal dari beberapa kolom kandidat secara berurutan
    (mis. pakai TANGGAL MULAI, kalau kosong fallback ke RENCANA MULAI)."""
    for col in columns:
        parsed = parse_date(row.get(col, ""))
        if parsed is not None:
            return parsed
    return None


def format_date(d) -> str:
    """Format objek date/datetime ke string standar untuk disimpan di Sheets."""
    if isinstance(d, (datetime, date)):
        return d.strftime("%d %b %Y")
    return ""