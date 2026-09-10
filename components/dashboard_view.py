import streamlit as st
import pandas as pd
from datetime import date
import plotly.graph_objects as go

from config import get_config

INDO_MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def _md(html_str: str) -> str:
    """Hilangkan leading whitespace di tiap baris HTML sebelum dikirim ke
    st.markdown(). Tanpa ini, baris yang diawali 4+ spasi (mengikuti indentasi
    kode Python di sekelilingnya) salah dikenali oleh parser Markdown sebagai
    *indented code block*, sehingga tag <div>/<svg> tampil sebagai teks mentah
    alih-alih dirender jadi elemen HTML (lihat bug kartu donut kejuruan)."""
    return "\n".join(line.strip() for line in html_str.strip().splitlines())

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
                _md(f"""
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span style="font-size: 22px;">⚠️</span>
                    <div>
                        <strong style="color: {c_theme['warning']}; font-size: 15px;">Peringatan Pengisian Survei Pelatihan (H-{h_days} Menuju Selesai)</strong>
                        <div style="font-size: 12.5px; color: {c_theme['text_secondary']};">
                            Ada <strong>{len(warning_programs)} program pelatihan</strong> yang mendekati masa akhir pelatihan (≤ {h_days} hari lagi). Harap arahkan siswa untuk segera mengisi kuesioner / survei evaluasi.
                        </div>
                    </div>
                </div>
                """),
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

def render_donut_svg(percent: float, c_theme: dict, size: int = 56, stroke: int = 8) -> str:
    """SVG donut/gauge ring sederhana untuk menampilkan persentase capaian
    per kejuruan, sesuai referensi desain koordinator."""
    percent = min(max(percent, 0), 100)
    radius = (size / 2) - (stroke / 2)
    circumference = 2 * 3.14159265 * radius
    offset = circumference * (1 - percent / 100)
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="flex-shrink:0;">
        <circle cx="{size/2}" cy="{size/2}" r="{radius}" fill="none"
                stroke="{c_theme['accent_soft']}" stroke-width="{stroke}"/>
        <circle cx="{size/2}" cy="{size/2}" r="{radius}" fill="none"
                stroke="{c_theme['accent']}" stroke-width="{stroke}"
                stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{offset:.2f}"
                stroke-linecap="round" transform="rotate(-90 {size/2} {size/2})"/>
    </svg>
    """


def render_stat_card(label: str, value: str, c_theme: dict, sublabel: str = "", highlight: bool = False):
    """Card statistik kecil untuk grid ringkasan (dipetakan dari wireframe:
    grid 2x2 kartu kecil di sebelah card yang di-highlight)."""
    border_style = f"2px solid {c_theme['accent']}" if highlight else f"1px solid {c_theme['border']}"
    with st.container(border=False):
        st.markdown(
            _md(f"""
            <div style="background:{c_theme['bg_surface']}; border:{border_style};
                        border-radius:12px; padding:16px 18px; height:118px;
                        display:flex; flex-direction:column; justify-content:space-between;
                        box-shadow:0 1px 2px rgba(0,0,0,0.06);">
                <div style="font-size:11.5px; font-weight:700; letter-spacing:0.03em;
                            text-transform:uppercase; color:{c_theme['text_secondary']};">
                    {label}
                </div>
                <div>
                    <div style="font-size:26px; font-weight:800; color:{c_theme['text_primary']}; line-height:1.1;">
                        {value}
                    </div>
                    {f'<div style="font-size:11.5px; color:{c_theme["text_secondary"]}; margin-top:2px;">{sublabel}</div>' if sublabel else ''}
                </div>
            </div>
            """),
            unsafe_allow_html=True,
        )


def render_kuota_card(title, total_paket, total_target_kuota, total_siswa_terisi, total_selesai, c_theme, sub_programs=None, kapasitas=16):
    """Ringkasan kuota per kejuruan — memakai style grid mini-card yang sama
    dengan ringkasan keseluruhan di atas, supaya konsisten secara visual."""
    persen_kuota = (total_siswa_terisi / total_target_kuota * 100) if total_target_kuota > 0 else 0.0
    sisa_kuota = max(0, total_target_kuota - total_siswa_terisi)

    st.markdown(f"**{title}**")

    col_highlight, col_grid = st.columns([1, 3])
    with col_highlight:
        st.markdown(
            _md(f"""
            <div style="background:{c_theme['bg_surface']}; border:2px solid {c_theme['accent']};
                        border-radius:12px; padding:14px 16px; height:118px;
                        display:flex; flex-direction:column; justify-content:space-between;
                        box-shadow:0 1px 2px rgba(0,0,0,0.06);">
                <div style="font-size:11px; font-weight:700; letter-spacing:0.03em;
                            text-transform:uppercase; color:{c_theme['text_secondary']};">
                    Capaian Kuota
                </div>
                <div style="font-size:24px; font-weight:800; color:{c_theme['accent']};">
                    {persen_kuota:.1f}%
                </div>
            </div>
            """),
            unsafe_allow_html=True,
        )
    with col_grid:
        m1, m2, m3 = st.columns(3)
        with m1:
            render_stat_card("Total Paket", f"{total_paket:,}".replace(",", "."), c_theme, "Paket")
        with m2:
            render_stat_card("Sisa Kuota", f"{sisa_kuota:,}".replace(",", "."), c_theme, "Siswa Belum Terisi")
        with m3:
            render_stat_card("Total Selesai", f"{total_selesai:,}".replace(",", "."), c_theme, "Paket (Check)")

    if sub_programs is not None and sub_programs.empty:
        st.caption("Belum ada program pelatihan tercatat untuk kategori ini.")
    elif sub_programs is not None and not sub_programs.empty:
        with st.expander(f"Lihat Rincian Program di {title} ({len(sub_programs)} Program)"):
            for _, prog in sub_programs.iterrows():
                p_target = prog["paket_sub"] * kapasitas
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
    # 1. BARIS ATAS: CARD HIGHLIGHT (donut besar, capaian keseluruhan) +
    #    GRID CARD DONUT PER KEJURUAN — sesuai referensi desain koordinator
    # ================================================================
    tot_paket = len(df)
    tot_target = tot_paket * KAPASITAS_DEFAULT
    tot_terisi = int(df["PESERTA"].sum())
    tot_persen = (tot_terisi / tot_target * 100) if tot_target > 0 else 0.0

    # Hitung capaian % per kejuruan untuk card donut
    per_bidang_persen = []
    for bidang in sorted([b for b in df["BIDANG"].dropna().unique() if str(b).strip()]):
        df_b = df[df["BIDANG"] == bidang]
        b_target = len(df_b) * KAPASITAS_DEFAULT
        b_terisi = int(df_b["PESERTA"].sum())
        b_persen = (b_terisi / b_target * 100) if b_target > 0 else 0.0
        per_bidang_persen.append((bidang, b_persen))

    col_highlight, col_grid = st.columns([1, 2.6])

    with col_highlight:
        st.markdown(
            _md(f"""
            <div style="background:{c_theme['bg_surface']}; border:2px solid {c_theme['accent']};
                        border-radius:12px; padding:18px; height:230px;
                        display:flex; flex-direction:column; justify-content:space-between;
                        box-shadow:0 1px 3px rgba(0,0,0,0.08);">
                <div style="font-size:11.5px; font-weight:700; letter-spacing:0.03em;
                            text-transform:uppercase; color:{c_theme['text_secondary']};">
                    Capaian Kuota Keseluruhan
                </div>
                <div style="display:flex; align-items:center; gap:14px;">
                    <div style="font-size:32px; font-weight:800; color:{c_theme['accent']};">
                        {tot_persen:.1f}%
                    </div>
                    {render_donut_svg(tot_persen, c_theme, size=68, stroke=9)}
                </div>
                <div style="font-size:12.5px; color:{c_theme['text_secondary']};">
                    {tot_terisi:,} / {tot_target:,} Siswa Terdaftar
                </div>
            </div>
            """.replace(",", ".")),
            unsafe_allow_html=True,
        )

    with col_grid:
        cards_html = "".join(
            _md(f"""
            <div style="background:{c_theme['bg_surface']}; border:1px solid {c_theme['border']};
                        border-radius:12px; padding:14px 16px; flex:1 1 160px; min-width:150px;
                        box-shadow:0 1px 2px rgba(0,0,0,0.06);">
                <div style="font-size:12.5px; font-weight:700; color:{c_theme['text_primary']};
                            margin-bottom:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;"
                     title="{bidang}">
                    {bidang}
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    {render_donut_svg(persen, c_theme, size=48, stroke=7)}
                    <div style="font-size:19px; font-weight:800; color:{c_theme['text_primary']};">
                        {persen:.1f}%
                    </div>
                </div>
            </div>
            """)
            for bidang, persen in per_bidang_persen
        )
        st.markdown(
            _md(f'<div style="display:flex; flex-wrap:wrap; gap:12px; height:230px; overflow-y:auto;">{cards_html}</div>'),
            unsafe_allow_html=True,
        )

    st.write("")

    # ================================================================
    # 2. BARIS BAWAH: BAR CHART KUOTA PER JURUSAN (kiri) berdampingan
    #    dengan GRAFIK JADWAL BULANAN (kanan, blok besar mengikuti
    #    wireframe)
    # ================================================================
    col_bar, col_month = st.columns([1.1, 1])

    with col_bar:
        st.markdown("#### Kuota Siswa per Kejuruan")
        st.caption("Terisi vs. sisa kuota per jurusan.")

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
            height=max(360, 42 * len(kuota_jurusan) + 60),
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

    with col_month:
        st.markdown("#### Jadwal Program per Bulan")
        st.caption("Bulan berjalan ditandai terpisah.")

        today = date.today()
        month_counts = pd.Series(0, index=range(1, 13))
        valid_months = df["_TGL_EFEKTIF"].dropna().apply(lambda d: d.month).value_counts()
        month_counts.update(valid_months)

        chart_df = pd.DataFrame({"Bulan": INDO_MONTHS, "Jumlah": month_counts.values, "bulan_ke": range(1, 13)})
        is_current = chart_df["bulan_ke"] == today.month
        marker_colors = [c_theme["accent"] if cur else c_theme["text_secondary"] for cur in is_current]
        marker_sizes = [14 if cur else 9 for cur in is_current]

        fig_bln = go.Figure()
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
                textfont=dict(color=c_theme["text_primary"], size=11),
                marker=dict(color=marker_colors, size=marker_sizes, line=dict(width=2, color=c_theme["bg_surface"])),
                hovertemplate="<b>%{y}</b><br>%{x} program pelatihan<extra></extra>",
                showlegend=False,
            )
        )

        fig_bln.update_layout(
            margin=dict(l=10, r=30, t=10, b=10),
            height=max(360, 42 * len(kuota_jurusan) + 60),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color=c_theme["text_secondary"], size=11),
            hoverlabel=dict(bgcolor=c_theme["bg_surface"], font_color=c_theme["text_primary"], bordercolor=c_theme["border"]),
            yaxis=dict(autorange="reversed", tickfont=dict(color=c_theme["text_primary"]), showgrid=False),
            xaxis=dict(showgrid=True, gridcolor=c_theme["grid"], tickfont=dict(color=c_theme["text_primary"]), zeroline=False),
            transition=dict(duration=400, easing="cubic-in-out"),
        )
        st.plotly_chart(fig_bln, width='stretch', config={"displayModeBar": False})

    st.write("")

    # ================================================================
    # 3. RINCIAN PER KEJURUAN (dipertahankan — tidak ada padanan di
    #    wireframe, tapi fungsinya penting & tidak diminta dihapus)
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
            sub_programs=sub_progs,
            kapasitas=KAPASITAS_DEFAULT,
        )
        st.write("")