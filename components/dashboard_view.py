import streamlit as st
import pandas as pd
from datetime import date
import plotly.graph_objects as go

from config import get_config

INDO_MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

def render_notification_h10(df: pd.DataFrame, c_theme: dict):
    """Mendeteksi program yang berada di rentang H-x sebelum selesai dan belum selesai (CHECK=False)."""
    today = date.today()
    h_days = get_config("h10_warning_days")

    # Filter program yang memiliki tanggal selesai dan belum selesai
    mask_h10 = (
        df["_TGL_SELESAI_EFEKTIF"].notna()
        & (~df["CHECK"])
    )
    df_active = df[mask_h10].copy()
    
    if df_active.empty:
        return

    # Hitung sisa hari menuju tanggal selesai
    df_active["sisa_hari"] = df_active["_TGL_SELESAI_EFEKTIF"].apply(lambda d: (d - today).days)

    # Ambil program yang berada di rentang 0 s.d. H-x hari sebelum selesai
    warning_programs = df_active[(df_active["sisa_hari"] >= 0) & (df_active["sisa_hari"] <= h_days)]
    
    if not warning_programs.empty:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span style="font-size: 22px;">⚠️</span>
                    <div>
                        <strong style="color: {c_theme['warning']}; font-size: 15px;">Peringatan Pengisian Survei Pelatihan (H-{h_days} Menuju Selesai)</strong>
                        <div style="font-size: 12.5px; color: {c_theme['text_secondary']};">
                            Ada <strong>{len(warning_programs)} program pelatihan</strong> yang mendekati masa akhir pelatihan (≤ {h_days} hari lagi). Harap arahkan siswa untuk segera mengisi kuesioner / survei evaluasi.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Tampilkan rincian kelas yang terkena warning
            for _, r in warning_programs.iterrows():
                hari_teks = "Hari ini selesai!" if r["sisa_hari"] == 0 else f"Sisa {r['sisa_hari']} hari lagi"
                tgl_str = r["_TGL_SELESAI_EFEKTIF"].strftime("%d %b %Y")
                
                c_info, c_badge = st.columns([4, 1])
                with c_info:
                    st.markdown(f"• **{r['PROGRAM PELATIHAN']}** ({r['BIDANG']} · {r['LOKASI'] if r['LOKASI'] else 'BPVP Kendari'})")
                    st.caption(f"Target Selesai: {tgl_str}")
                with c_badge:
                    st.markdown(
                        f"<div style='text-align:right; padding-top:4px;'><span style='background:{c_theme['warning']}; color:#FFFFFF; font-weight:700; font-size:11px; padding:3px 8px; border-radius:6px;'>{hari_teks}</span></div>",
                        unsafe_allow_html=True
                    )
            st.divider()

def render_kuota_card(title, total_paket, total_target_kuota, total_siswa_terisi, total_selesai, c_theme, sub_programs=None):
    """Komponen Card Target & Capaian Kuota Pelatihan Siswa."""
    persen_kuota = (total_siswa_terisi / total_target_kuota * 100) if total_target_kuota > 0 else 0.0
    sisa_kuota = max(0, total_target_kuota - total_siswa_terisi)

    with st.container(border=True):
        head_col, pct_col = st.columns([3, 1])
        with head_col:
            st.caption(title.upper())
            st.markdown(
                f"## {total_siswa_terisi:,}".replace(",", ".")
                + f" <span style='font-size:18px; color:{c_theme['text_secondary']};'>/ "
                + f"{total_target_kuota:,}".replace(",", ".")
                + " Siswa Terdaftar</span>",
                unsafe_allow_html=True,
            )
        with pct_col:
            st.metric(label="Capaian Kuota", value=f"{persen_kuota:.1f}%")

        st.progress(min(max(persen_kuota / 100.0, 0.0), 1.0))
        st.divider()

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Paket Pelatihan", f"{total_paket:,}".replace(",", ".") + " Paket")
        with m2:
            st.metric("Sisa Kuota Belum Terisi", f"{sisa_kuota:,}".replace(",", ".") + " Siswa")
        with m3:
            st.metric("Total Selesai (Check)", f"{total_selesai:,}".replace(",", ".") + " Paket")

        if sub_programs is not None and sub_programs.empty:
            st.caption("Belum ada program pelatihan tercatat untuk kategori ini.")
        elif sub_programs is not None and not sub_programs.empty:
            with st.expander(f"Lihat Rincian Program di {title} ({len(sub_programs)} Program)"):
                for _, prog in sub_programs.iterrows():
                    p_target = prog["paket_sub"] * 16
                    p_terisi = int(prog["peserta_sub"])
                    p_pct = (p_terisi / p_target * 100) if p_target > 0 else 0.0

                    c_left, c_right = st.columns([3, 1])
                    with c_left:
                        st.markdown(f"**{prog['PROGRAM PELATIHAN']}**")
                        lok = prog["LOKASI"] if prog["LOKASI"] else "BPVP Kendari"
                        st.caption(f"Lokasi: {lok} · {p_terisi} / {p_target} Peserta · {int(prog['selesai_sub'])} Paket Selesai")
                    with c_right:
                        st.markdown(f"**{p_pct:.1f}%**")

                    st.progress(min(max(p_pct / 100.0, 0.0), 1.0))
                    st.write("")

def render_dashboard(df: pd.DataFrame, c_theme: dict):
    if df.empty:
        st.info(
            "Tidak ada data yang cocok dengan filter yang dipilih. "
            "Coba ubah atau reset filter di sidebar untuk melihat data lain."
        )
        return

    KAPASITAS_DEFAULT = get_config("kapasitas_default")

    # ================================================================
    # 0. NOTIFIKASI PERINGATAN H-10 SURVEI SISWA
    # ================================================================
    if "_TGL_SELESAI_EFEKTIF" in df.columns:
        render_notification_h10(df, c_theme)

    # ================================================================
    # 1. CARD UTAMA: KESELURUHAN (SEMUA JURUSAN)
    # ================================================================
    tot_paket = len(df)
    tot_target = tot_paket * KAPASITAS_DEFAULT
    tot_terisi = int(df["PESERTA"].sum())
    tot_selesai = int(df["CHECK"].sum())

    render_kuota_card(
        title="Target & Capaian Kuota Pelatihan Siswa (Keseluruhan)",
        total_paket=tot_paket,
        total_target_kuota=tot_target,
        total_siswa_terisi=tot_terisi,
        total_selesai=tot_selesai,
        c_theme=c_theme
    )

    st.write("")

    # ================================================================
    # 2. GRAFIK BATANG HORIZONTAL KUOTA JURUSAN (KANAN KE KIRI)
    # ================================================================
    st.markdown("#### Kuota Siswa per Kejuruan")
    st.caption("Terisi vs. sisa kuota per jurusan. Arahkan kursor ke batang untuk rincian, klik legenda untuk sembunyikan salah satu.")

    kuota_jurusan = (
        df.groupby("BIDANG")
        .agg(paket=("PROGRAM PELATIHAN", "count"), terisi=("PESERTA", "sum"))
        .reset_index()
    )
    kuota_jurusan["kuota_target"] = kuota_jurusan["paket"] * KAPASITAS_DEFAULT
    kuota_jurusan["terisi"] = kuota_jurusan["terisi"].clip(upper=kuota_jurusan["kuota_target"])
    kuota_jurusan["sisa"] = (kuota_jurusan["kuota_target"] - kuota_jurusan["terisi"]).clip(lower=0)
    kuota_jurusan["pct"] = (kuota_jurusan["terisi"] / kuota_jurusan["kuota_target"] * 100).where(kuota_jurusan["kuota_target"] > 0, 0)
    kuota_jurusan = kuota_jurusan.sort_values(by="kuota_target", ascending=True)

    fig_rtl = go.Figure()
    fig_rtl.add_trace(
        go.Bar(
            name="Terisi",
            y=kuota_jurusan["BIDANG"],
            x=kuota_jurusan["terisi"],
            orientation="h",
            marker=dict(color=c_theme["accent"], line=dict(width=0)),
            customdata=kuota_jurusan["pct"],
            hovertemplate="<b>%{y}</b><br>Terisi: %{x:,.0f} siswa<br>Capaian: %{customdata:.1f}%<extra></extra>",
        )
    )
    fig_rtl.add_trace(
        go.Bar(
            name="Sisa Kuota",
            y=kuota_jurusan["BIDANG"],
            x=kuota_jurusan["sisa"],
            orientation="h",
            marker=dict(color=c_theme["accent_soft"], line=dict(width=0)),
            hovertemplate="<b>%{y}</b><br>Sisa: %{x:,.0f} siswa<extra></extra>",
        )
    )

    fig_rtl.update_layout(
        barmode="stack",
        margin=dict(l=10, r=15, t=10, b=10),
        height=max(280, 42 * len(kuota_jurusan) + 60),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=c_theme["text_secondary"], size=12),
        hovermode="closest",
        hoverlabel=dict(bgcolor=c_theme["bg_surface"], font_color=c_theme["text_primary"], bordercolor=c_theme["border"]),
        bargap=0.35,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color=c_theme["text_secondary"])),
        xaxis=dict(
            showgrid=True,
            gridcolor=c_theme["grid"],
            tickfont=dict(color=c_theme["text_primary"]),
        ),
        yaxis=dict(tickfont=dict(color=c_theme["text_primary"])),
        transition=dict(duration=400, easing="cubic-in-out"),
    )
    st.plotly_chart(fig_rtl, width='stretch', config={"displayModeBar": False})

    st.write("")

    # ================================================================
    # 3. CARD KUOTA PER MASING-MASING KEJURUAN (BIDANG)
    # ================================================================
    st.markdown("#### Target & Capaian Kuota per Kejuruan")
    st.caption("Monitoring kuota siswa terpisah untuk masing-masing bidang pelatihan vokasi.")

    bidang_list = sorted([b for b in df["BIDANG"].dropna().unique() if str(b).strip()])

    for bidang in bidang_list:
        df_bidang = df[df["BIDANG"] == bidang]
        b_paket = len(df_bidang)
        b_target = b_paket * KAPASITAS_DEFAULT
        b_terisi = int(df_bidang["PESERTA"].sum())
        b_selesai = int(df_bidang["CHECK"].sum())

        sub_progs = (
            df_bidang.groupby(["PROGRAM PELATIHAN", "LOKASI"])
            .agg(
                paket_sub=("NO", "count"),
                peserta_sub=("PESERTA", "sum"),
                selesai_sub=("CHECK", "sum")
            )
            .reset_index()
        )

        render_kuota_card(
            title=f"Kejuruan: {bidang}",
            total_paket=b_paket,
            total_target_kuota=b_target,
            total_siswa_terisi=b_terisi,
            total_selesai=b_selesai,
            c_theme=c_theme,
            sub_programs=sub_progs
        )

    st.write("")

    # ================================================================
    # 4. GRAFIK JADWAL BULANAN (HORIZONTAL)
    # ================================================================
    st.markdown("#### Jadwal Program Pelatihan per Bulan")
    st.caption("Bulan berjalan ditandai terpisah. Arahkan kursor ke titik untuk melihat jumlah program.")

    today = date.today()
    month_counts = pd.Series(0, index=range(1, 13))
    valid_months = df["_TGL_EFEKTIF"].dropna().apply(lambda d: d.month).value_counts()
    month_counts.update(valid_months)

    chart_df = pd.DataFrame({"Bulan": INDO_MONTHS, "Jumlah": month_counts.values, "bulan_ke": range(1, 13)})
    is_current = chart_df["bulan_ke"] == today.month
    marker_colors = [c_theme["accent"] if cur else c_theme["text_secondary"] for cur in is_current]
    marker_sizes = [16 if cur else 11 for cur in is_current]

    fig_bln = go.Figure()
    # Garis batang tipis (stem) dari 0 ke nilai — kesan "lollipop", bukan blok solid
    for _, row in chart_df.iterrows():
        cur = row["bulan_ke"] == today.month
        fig_bln.add_shape(
            type="line",
            x0=0, x1=row["Jumlah"], y0=row["Bulan"], y1=row["Bulan"],
            line=dict(color=c_theme["accent"] if cur else c_theme["border"], width=3),
        )

    fig_bln.add_trace(
        go.Scatter(
            y=chart_df["Bulan"],
            x=chart_df["Jumlah"],
            mode="markers+text",
            text=chart_df["Jumlah"],
            textposition="middle right",
            textfont=dict(color=c_theme["text_primary"], size=12),
            marker=dict(color=marker_colors, size=marker_sizes, line=dict(width=2, color=c_theme["bg_surface"])),
            hovertemplate="<b>%{y}</b><br>%{x} program pelatihan<extra></extra>",
            showlegend=False,
        )
    )

    fig_bln.update_layout(
        margin=dict(l=10, r=40, t=10, b=10),
        height=340,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=c_theme["text_secondary"], size=12),
        hoverlabel=dict(bgcolor=c_theme["bg_surface"], font_color=c_theme["text_primary"], bordercolor=c_theme["border"]),
        yaxis=dict(autorange="reversed", tickfont=dict(color=c_theme["text_primary"]), showgrid=False),
        xaxis=dict(showgrid=True, gridcolor=c_theme["grid"], tickfont=dict(color=c_theme["text_primary"]), zeroline=False),
        transition=dict(duration=400, easing="cubic-in-out"),
    )
    st.plotly_chart(fig_bln, width='stretch', config={"displayModeBar": False})