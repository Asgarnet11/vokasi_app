"""Konfigurasi aplikasi. Nilai bisa dioverride lewat st.secrets["app_config"]
tanpa perlu mengubah kode."""
import streamlit as st

_defaults = {
    "kapasitas_default": 16,
    "worksheet_name": "Reg",
    "cache_ttl_seconds": 30,
    "h10_warning_days": 10,
}


def get_config(key: str):
    try:
        overrides = dict(st.secrets.get("app_config", {}))
    except Exception:
        overrides = {}
    return overrides.get(key, _defaults[key])