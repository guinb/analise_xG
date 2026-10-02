# -*- coding: utf-8 -*-
"""
View 1: Raio-X & Panorama Geral do Palmeiras.
Apresenta a identidade estatística consolidada do Palmeiras no recorte selecionado:
- Cards de Identidade (Aproveitamento, xG Pró/Contra, Gols, Posse, Field Tilt)
- Linha do Tempo de Rendimento (xG Pró vs xG Contra jogo a jogo)
- Mapa Espacial de Finalizações no Campo (Shotmap)
- Fases de Criação (Jogo Aberto vs Bola Parada vs Transição)
- Top Finalizadores e Artilheiros
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def render_overview_view(df_shots: pd.DataFrame, df_matches: pd.DataFrame):
    st.markdown("### 📊 Raio-X & Panorama Geral do Palmeiras")
    st.caption("Visão estatística 360° consolidada da equipe para o recorte selecionado na barra lateral.")

    if df_matches.empty:
        st.warning("Nenhuma partida encontrada para os filtros selecionados.")
        return

    pal_shots = df_shots[df_shots["is_palmeiras"] == True].copy()
    n_matches = len(df_matches)
    n_shots = len(pal_shots)

    # -------------------------------------------------------------------------
    # 1. CARDS DE IDENTIDADE ESTATÍSTICA (CLAROS E EXPLICATIVOS)
    # -------------------------------------------------------------------------
    vits = (df_matches["result"] == "Vitória").sum()
    emps = (df_matches["result"] == "Empate").sum()
    derrs = (df_matches["result"] == "Derrota").sum()
    aprov = ((vits * 3 + emps) / (n_matches * 3) * 100) if n_matches > 0 else 0

    gols_pro = int(df_matches["palmeiras_goals"].sum())
    gols_contra = int(df_matches["opponent_goals"].sum())
    xg_pro = df_matches["palmeiras_xg"].sum()
    xg_contra = df_matches["opponent_xg"].sum()

    posse_media = df_matches["palmeiras_possession"].mean() if "palmeiras_possession" in df_matches.columns else 0
    field_tilt = df_matches["field_tilt"].mean() if "field_tilt" in df_matches.columns else 0
    saldo_letalidade = gols_pro - xg_pro
    saldo_defensivo = xg_contra - gols_contra

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div style="background:#161f30; border:1px solid #2d3a56; border-radius:8px; padding:14px;">
                <div style="color:#9bb0cf; font-size:0.82rem; font-weight:600; text-transform:uppercase;">🏆 Aproveitamento</div>
                <div style="font-size:1.9rem; font-weight:800; color:#00FF87; margin:4px 0;">{aprov:.1f}%</div>
                <div style="font-size:0.88rem; color:#E2E8F0; font-weight:600;">{vits}V - {emps}E - {derrs}D <span style="color:#94A3B8;">({n_matches} jogos)</span></div>
                <div style="font-size:0.78rem; color:#94A3B8; margin-top:4px;">Taxa de vitórias: <b>{(vits/n_matches*100):.1f}%</b> ({((vits*3+emps)/n_matches):.2f} pts/j)</div>
            </div>
            """, unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div style="background:#161f30; border:1px solid #2d3a56; border-radius:8px; padding:14px;">
                <div style="color:#9bb0cf; font-size:0.82rem; font-weight:600; text-transform:uppercase;">⚔️ Ataque (Gols vs xG)</div>
                <div style="font-size:1.9rem; font-weight:800; color:#38BDF8; margin:4px 0;">{gols_pro / n_matches:.2f} <span style="font-size:1rem; font-weight:400; color:#94A3B8;">gols/j</span></div>
                <div style="font-size:0.88rem; color:#E2E8F0; font-weight:600;">Total: {gols_pro} gols <span style="color:#94A3B8;">(xG: {xg_pro:.1f})</span></div>
                <div style="font-size:0.78rem; color:{'#00FF87' if saldo_letalidade>=0 else '#FF4B4B'}; margin-top:4px;">
                    Letalidade: <b>{saldo_letalidade:+.1f} gols</b> vs expectativa de xG
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""
            <div style="background:#161f30; border:1px solid #2d3a56; border-radius:8px; padding:14px;">
                <div style="color:#9bb0cf; font-size:0.82rem; font-weight:600; text-transform:uppercase;">🛡️ Solidez Defensiva</div>
                <div style="font-size:1.9rem; font-weight:800; color:{'#00FF87' if (gols_contra/n_matches)<=1.0 else '#FF4B4B'}; margin:4px 0;">{gols_contra / n_matches:.2f} <span style="font-size:1rem; font-weight:400; color:#94A3B8;">sofridos/j</span></div>
                <div style="font-size:0.88rem; color:#E2E8F0; font-weight:600;">Total: {gols_contra} sofridos <span style="color:#94A3B8;">(xG cedido: {xg_contra:.1f})</span></div>
                <div style="font-size:0.78rem; color:{'#00FF87' if saldo_defensivo>=0 else '#FF4B4B'}; margin-top:4px;">
                    Gols salvos: <b>{saldo_defensivo:+.1f}</b> pelo goleiro/zaga
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""
            <div style="background:#161f30; border:1px solid #2d3a56; border-radius:8px; padding:14px;">
                <div style="color:#9bb0cf; font-size:0.82rem; font-weight:600; text-transform:uppercase;">🏟️ Domínio Territorial</div>
                <div style="font-size:1.9rem; font-weight:800; color:#F59E0B; margin:4px 0;">{field_tilt:.1f}% <span style="font-size:0.95rem; font-weight:400; color:#94A3B8;">Tilt</span></div>
                <div style="font-size:0.88rem; color:#E2E8F0; font-weight:600;">Posse Média: <b>{posse_media:.1f}%</b></div>
                <div style="font-size:0.78rem; color:#94A3B8; margin-top:4px;">
                    { 'Sufocamento no terço rival (>55%)' if field_tilt>=55 else ('Controle moderado (50-55%)' if field_tilt>=50 else 'Estratégia mais reativa (<50%)') }
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 2. LINHA DO TEMPO DE RENDIMENTO (JOGO A JOGO)
    # -------------------------------------------------------------------------
    st.markdown("#### 📈 Evolução do Rendimento Jogo a Jogo")
    st.caption("Acompanhe o perigo criado (xG Pró) versus o perigo sofrido (xG Contra) ao longo da temporada.")

    matches_sorted = df_matches.sort_values(by="date").copy()
    matches_sorted["label_jogo"] = matches_sorted["date"].astype(str) + " (" + matches_sorted["opponent_name"].astype(str) + ")"

    fig_timeline = go.Figure()
    fig_timeline.add_trace(go.Scatter(
        x=matches_sorted["label_jogo"], y=matches_sorted["palmeiras_xg"].round(2),
        name="xG Pró (Criação)", mode="lines+markers",
        line=dict(color="#00FF87", width=2.5),
        marker=dict(size=6)
    ))
    fig_timeline.add_trace(go.Scatter(
        x=matches_sorted["label_jogo"], y=matches_sorted["opponent_xg"].round(2),
        name="xG Contra (Defesa)", mode="lines+markers",
        line=dict(color="#FF4B4B", width=2, dash="dot"),
        marker=dict(size=5)
    ))
    fig_timeline.update_layout(
        template="plotly_dark", height=380,
        margin=dict(l=10, r=10, t=30, b=60),
        yaxis_title="Gols Esperados (xG)",
        xaxis=dict(tickangle=-45, nticks=15),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. MAPA ESPACIAL VERTICAL & FASES DE CRIAÇÃO (ATAQUE & DEFESA)
    # -------------------------------------------------------------------------
    def draw_vertical_shotmap_pitch(df_shots_subset: pd.DataFrame) -> go.Figure:
        fig = go.Figure()
        line_color = "rgba(255, 255, 255, 0.4)"
        grass_color = "#0e1117"

        # Campo vertical FIFA (X: 0 a 68m, Y: 52.5 a 105m - atacando para o topo)
        fig.add_shape(type="rect", x0=0, y0=52.5, x1=68, y1=105, line=dict(color=line_color, width=2), fillcolor=grass_color, layer="below")
        fig.add_shape(type="line", x0=0, y0=52.5, x1=68, y1=52.5, line=dict(color=line_color, width=2), layer="below")
        fig.add_shape(type="rect", x0=13.84, y0=88.5, x1=54.16, y1=105.0, line=dict(color=line_color, width=1.5), layer="below")
        fig.add_shape(type="rect", x0=24.84, y0=99.5, x1=43.16, y1=105.0, line=dict(color=line_color, width=1.5), layer="below")
        fig.add_shape(type="circle", x0=33.6, y0=93.6, x1=34.4, y1=94.4, fillcolor="#FFFFFF", line_color="#FFFFFF", layer="below")
        fig.add_shape(type="rect", x0=30.34, y0=105.0, x1=37.66, y1=106.8, line=dict(color="#00FF87", width=3), layer="below")

        theta = np.linspace(np.pi * 0.20, np.pi * 0.80, 30)
        arc_x = 34.0 + 9.15 * np.cos(theta)
        arc_y = 94.0 - 9.15 * np.sin(theta)
        fig.add_trace(go.Scatter(x=arc_x, y=arc_y, mode="lines", line=dict(color=line_color, width=1.5), hoverinfo="skip", showlegend=False))

        if not df_shots_subset.empty and "x_pct" in df_shots_subset.columns and "y_pct" in df_shots_subset.columns:
            shots = df_shots_subset.copy()
            shots["pitch_x"] = (shots["y_pct"] / 100.0) * 68.0
            shots["pitch_y"] = 105.0 - (shots["x_pct"] * 1.05)
            shots["marker_size"] = np.clip(np.sqrt(shots["xg"]) * 34, 6, 28)

            outcome_colors = {
                "Gol": "#00FF87",
                "Defesa": "#00BFFF",
                "Para Fora": "#FF4B4B",
                "Bloqueado": "#FFA500",
                "Trave": "#FFD700"
            }

            for outcome, col in outcome_colors.items():
                sub = shots[shots["outcome"] == outcome]
                if sub.empty:
                    continue
                hover_text = []
                for _, r in sub.iterrows():
                    xgot_str = f"{r.get('xgot', 0.0):.3f}" if pd.notnull(r.get('xgot')) else "N/A"
                    txt = (
                        f"<b>{r['player_name']}</b> ({r['shooter_team']})<br>"
                        f"Minuto: {r['minute']}'<br>"
                        f"xG: <b>{r['xg']:.3f}</b> | xGOT: {xgot_str}<br>"
                        f"Desfecho: <b>{r['outcome']}</b> | Situação: {r['situation']}<br>"
                        f"Distância: {r.get('distance_meters', 0.0):.1f}m"
                    )
                    hover_text.append(txt)

                fig.add_trace(go.Scatter(
                    x=sub["pitch_x"], y=sub["pitch_y"],
                    mode="markers", name=outcome,
                    marker=dict(
                        size=sub["marker_size"], color=col, opacity=0.85,
                        line=dict(color="#FFFFFF" if outcome == "Gol" else "#0A1E11", width=1.5 if outcome == "Gol" else 0.8)
                    ),
                    text=hover_text, hoverinfo="text"
                ))

        fig.update_xaxes(range=[-2, 70], showgrid=False, zeroline=False, showticklabels=False, fixedrange=True)
        fig.update_yaxes(range=[50, 108], showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1, fixedrange=True)
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor=grass_color,
            paper_bgcolor=grass_color,
            height=490,
            margin=dict(l=10, r=10, t=10, b=30),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.03,
                xanchor="center",
                x=0.5,
                font=dict(color="#FFFFFF", size=10.5)
            )
        )
        return fig

    c_hdr, c_persp = st.columns([1.1, 1.9])
    with c_hdr:
        st.markdown("#### 🎯 Dinâmica Espacial & Criação")
    with c_persp:
        persp_choice = st.radio(
            "Perspectiva de Análise:",
            ["⚔️ Ataque (Finalizações do Palmeiras)", "🛡️ Defesa (Finalizações Sofridas / Concedidas)"],
            horizontal=True,
            key="v1_shotmap_persp"
        )

    is_atk = "Ataque" in persp_choice
    active_shots = df_shots[df_shots["is_palmeiras"] == is_atk].copy()

    col_map, col_phase = st.columns([1.15, 0.85])

    with col_map:
        if is_atk:
            st.markdown("##### ⚽ Mapa de Chutes do Palmeiras (Ataque)")
            st.caption("Orientação vertical (atacando para o topo). Bolhas = xG; Cor = desfecho.")
        else:
            st.markdown("##### 🛡️ Mapa de Chutes Concedidos (Defesa)")
            st.caption("Finalizações sofridas pela zaga no nosso campo. Bolhas = perigo rival.")

        fig_pitch = draw_vertical_shotmap_pitch(active_shots)
        st.plotly_chart(fig_pitch, use_container_width=True)

    with col_phase:
        if is_atk:
            st.markdown("##### 🧩 Fases da Criação Ofensiva")
            st.caption("Como o Palmeiras constrói suas chances de gol.")
            scale_col = "Greens"
        else:
            st.markdown("##### 🧩 Como os Rivais Criam Perigo")
            st.caption("Origem dos chutes sofridos pela zaga palmeirense.")
            scale_col = "Reds"

        if not active_shots.empty and "situation" in active_shots.columns:
            phase_df = active_shots.groupby("situation").agg(
                xg_sum=("xg", "sum"), chutes=("shot_id", "count")
            ).reset_index()
            phase_df["pct_xg"] = (phase_df["xg_sum"] / max(0.001, phase_df["xg_sum"].sum()) * 100).round(1)
            phase_df_sorted = phase_df.sort_values(by="pct_xg", ascending=True)

            # Use explicit bar colors based on perspective — no continuous scale
            # Attack: green tones; Defense: red tones. Discrete for visibility on dark background.
            if is_atk:
                _palette = ["#1a6b3c", "#2a9d5c", "#00c96d", "#00FF87", "#7fffd4"]
            else:
                _palette = ["#6b1a1a", "#c43b3b", "#FF4B4B", "#ff7777", "#ffaaaa"]
            _n = len(phase_df_sorted)
            _colors = _palette[:_n] if _n <= len(_palette) else _palette * (_n // len(_palette) + 1)

            fig_phase = go.Figure(go.Bar(
                x=phase_df_sorted["pct_xg"],
                y=phase_df_sorted["situation"],
                orientation="h",
                marker_color=_colors[:_n],
                text=[f"{v:.1f}%" for v in phase_df_sorted["pct_xg"]],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>%{x:.1f}% do xG total<extra></extra>"
            ))
            fig_phase.update_layout(
                template="plotly_dark",
                height=490, margin=dict(l=10, r=30, t=10, b=30), showlegend=False,
                xaxis=dict(title="% do xG Total", range=[0, phase_df_sorted["pct_xg"].max() * 1.3])
            )
            st.plotly_chart(fig_phase, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 4. TOP FINALIZADORES & PROTAGONISTAS DO PERÍODO
    # -------------------------------------------------------------------------
    if is_atk:
        st.markdown("#### 👟 Principais Finalizadores do Palmeiras no Recorte")
    else:
        st.markdown("#### ⚠️ Atacantes Rivais Mais Perigosos contra o Palmeiras")

    if not active_shots.empty:
        player_agg = active_shots.groupby("player_name").agg(
            chutes=("shot_id", "count"),
            gols=("is_goal", "sum"),
            xg_total=("xg", "sum")
        ).reset_index()
        player_agg["xg_por_chute"] = (player_agg["xg_total"] / player_agg["chutes"]).round(3)
        player_agg["letalidade"] = (player_agg["gols"] - player_agg["xg_total"]).round(2)
        player_agg["xg_total"] = player_agg["xg_total"].round(2)

        top_scorers = player_agg.sort_values(by="xg_total", ascending=False).head(10).rename(columns={
            "player_name": "Atleta",
            "chutes": "Finalizações",
            "gols": "Gols",
            "xg_total": "xG Acumulado",
            "xg_por_chute": "xG / Chute",
            "letalidade": "Saldo Letalidade (G - xG)"
        })
        st.dataframe(top_scorers, use_container_width=True, hide_index=True)
