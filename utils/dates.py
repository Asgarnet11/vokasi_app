"""
Utilitas parsing & formatting tanggal terpusat.

Mendukung format tanggal Indonesia maupun standar internasional (ISO),
termasuk singkatan dan nama lengkap bulan dalam bahasa Indonesia (mis. Agu, Okt, Mei, Des).
"""
import re
from datetime import datetime, date

# Pemetaan nama & singkatan bulan bahasa Indonesia ke bahasa Inggris
# agar datetime.strptime di lingkungan locale English (default Linux/Cloud)
# dapat memprosesnya dengan akurat.
INDO_MONTH_MAP = {
    "januari": "January", "jan": "Jan",
    "februari": "February", "feb": "Feb",
    "maret": "March", "mar": "Mar",
    "april": "April", "apr": "Apr",
    "mei": "May",
    "juni": "June", "jun": "Jun",
    "juli": "July", "jul": "Jul",
    "agustus": "August", "agu": "Aug", "agt": "Aug",
    "september": "September", "sep": "Sep",
    "oktober": "October", "okt": "Oct",
    "november": "November", "nov": "Nov",
    "desember": "December", "des": "Dec",
}

# Regex pattern untuk mengganti nama bulan Indonesia
_MONTH_REGEX = re.compile(
    r"\b(" + "|".join(INDO_MONTH_MAP.keys()) + r")\b",
    re.IGNORECASE
)

DATE_FORMATS = [
    "%d %b %Y",
    "%d %B %Y",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
]


def normalize_date_string(value: str) -> str:
    """Normalisasi string tanggal, ubah nama bulan Indonesia ke bahasa Inggris."""
    if not value:
        return ""
    val_clean = str(value).strip()
    return _MONTH_REGEX.sub(lambda m: INDO_MONTH_MAP[m.group(0).lower()], val_clean)


def parse_date(value) -> date | None:
    """Parse string tanggal ke objek date, coba semua format yang didukung.
    Mendukung format Indonesia maupun ISO. Mengembalikan None jika gagal."""
    if value is None or (isinstance(value, float) and str(value) == "nan"):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    val = normalize_date_string(str(value))
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