"""
Módulo de Comparação Tática (Modo A vs B):
Permite comparar diretamente dois períodos ou recortes:
- Temporada 2026 vs Temporada 2025
- Brasileirão 2026: 1º Turno vs 2º Turno
- Competições (ex: Brasileirão vs Libertadores)
Exibe deltas de indicadores, gráfico radar tático de 6 eixos, decomposição fatorial e mapas comparativos.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from src.visualization.pitch_density import plot_density_shotmap, plot_tactical_zones_pitch
from src.visualization.pitch_plotly import plot_interactive_shotmap

def filter_dataset_by_preset(df_matches: pd.DataFrame, df_shots: pd.DataFrame, preset_type: str, preset_val: str):
    m_sub = df_matches.copy()
    s_sub = df_shots.copy()

    if preset_type == "Temporada Completa":
        m_sub = m_sub[m_sub["season"] == preset_val]
        s_sub = s_sub[s_sub["season"] == preset_val]
    elif preset_type == "Turno do Brasileirão":
        # Formato: "2026 - 1º Turno"
        parts = preset_val.split(" - ")
        yr = parts[0]
        turno = parts[1]
        m_sub = m_sub[(m_sub["season"] == yr) & (m_sub["tournament"].str.contains("Brasileir", case=False)) & (m_sub["turno"] == turno)]
        s_sub = s_sub[(s_sub["season"] == yr) & (s_sub["tournament"].str.contains("Brasileir", case=False)) & (s_sub["turno"] == turno)]
    elif preset_type == "Competição":
        m_sub = m_sub[m_sub["tournament"] == preset_val]
        s_sub = s_sub[s_sub["tournament"] == preset_val]

    return m_sub, s_sub

def compute_profile_metrics(m_sub: pd.DataFrame, s_sub: pd.DataFrame):
    pal_s = s_sub[s_sub["is_palmeiras"] == True]
    n_matches = m_sub["match_id"].nunique()
    total_shots = len(pal_s)
    total_xg = pal_s["xg"].sum()
    total_goals = pal_s["is_goal"].sum()

    shots_p90 = total_shots / n_matches if n_matches > 0 else 0
    xg_p90 = total_xg / n_matches if n_matches > 0 else 0
    xg_p_shot = total_xg / total_shots if total_shots > 0 else 0
    goals_p90 = total_goals / n_matches if n_matches > 0 else 0
    conv_pct = (total_goals / total_shots * 100) if total_shots > 0 else 0
    avg_dist = pal_s["distance_meters"].mean() if total_shots > 0 else 0
    
    # % de xG em jogo aberto
    open_play_xg = pal_s[pal_s["situation"] == "Jogo Aberto"]["xg"].sum()
    pct_open_play = (open_play_xg / total_xg * 100) if total_xg > 0 else 0

    # % de chutes de grande chance
    high_danger_count = (pal_s["xg_danger"] == "Alta (>=0.30)").sum()
    pct_high_danger = (high_danger_count / total_shots * 100) if total_shots > 0 else 0

    # Métricas táticas e territoriais
    avg_field_tilt = float(m_sub["field_tilt"].mean()) if "field_tilt" in m_sub and not m_sub["field_tilt"].isna().all() else 50.0
    avg_touches_box = float(m_sub["palmeiras_touches_in_box"].mean()) if "palmeiras_touches_in_box" in m_sub and not m_sub["palmeiras_touches_in_box"].isna().all() else 0.0
    avg_crosses = float(m_sub["palmeiras_crosses_attempted"].mean()) if "palmeiras_crosses_attempted" in m_sub and not m_sub["palmeiras_crosses_attempted"].isna().all() else 0.0
    avg_possession = float(m_sub["palmeiras_possession"].mean()) if "palmeiras_possession" in m_sub and not m_sub["palmeiras_possession"].isna().all() else 50.0

    return {
        "n_matches": n_matches,
        "total_shots": total_shots,
        "total_xg": total_xg,
        "total_goals": total_goals,
        "shots_p90": shots_p90,
        "xg_p90": xg_p90,
        "xg_p_shot": xg_p_shot,
        "goals_p90": goals_p90,
        "conv_pct": conv_pct,
        "avg_dist": avg_dist,
        "pct_open_play": pct_open_play,
        "pct_high_danger": pct_high_danger,
        "avg_field_tilt": avg_field_tilt,
        "avg_touches_box": avg_touches_box,
        "avg_crosses": avg_crosses,
        "avg_possession": avg_possession
    }

def render_comparison_view(df_shots: pd.DataFrame, df_matches: pd.DataFrame):
    st.markdown("### ⚔️ Modo Comparação Tática: Cenário A vs. Cenário B")
    st.info(
        "💡 **Modo Comparativo:** Compare diretamente dois períodos ou turnos distintos. "
        "Avalie se houve ganho ou perda de volume de chutes, qualidade média, distância ou estilo de jogo."
    )

    # Criar listas de opções
    available_seasons = sorted(list(df_matches["season"].dropna().unique()), reverse=True)
    all_tournaments = sorted(list(df_matches["tournament"].dropna().unique()))
    
    # Opções de Turnos do Brasileirão
    bra_matches = df_matches[df_matches["tournament"].str.contains("Brasileir", case=False)]
    turno_options = []
    for s_yr in available_seasons:
        sub = bra_matches[bra_matches["season"] == s_yr]
        turnos_in_season = sub["turno"].unique()
        for t in ["1º Turno", "2º Turno"]:
            if t in turnos_in_season:
                turno_options.append(f"{s_yr} - {t}")

    preset_categories = ["Temporada Completa", "Turno do Brasileirão", "Competição"]

    c_box_a, c_box_b = st.columns([1, 1])

    with c_box_a:
        st.markdown("#### 🔵 Cenário A (Referência)")
        type_a = st.selectbox("Tipo de Recorte A:", preset_categories, index=0, key="type_a")
        if type_a == "Temporada Completa":
            val_a = st.selectbox("Selecione a Temporada A:", available_seasons, index=min(1, len(available_seasons)-1), key="val_a")
        elif type_a == "Turno do Brasileirão":
            val_a = st.selectbox("Selecione o Turno A:", turno_options, index=min(1, len(turno_options)-1), key="val_a")
        else:
            val_a = st.selectbox("Selecione a Competição A:", all_tournaments, index=0, key="val_a")

    with c_box_b:
        st.markdown("#### 🟢 Cenário B (Comparação)")
        type_b = st.selectbox("Tipo de Recorte B:", preset_categories, index=0, key="type_b")
        if type_b == "Temporada Completa":
            val_b = st.selectbox("Selecione a Temporada B:", available_seasons, index=0, key="val_b")
        elif type_b == "Turno do Brasileirão":
            val_b = st.selectbox("Selecione o Turno B:", turno_options, index=0, key="val_b")
        else:
            val_b = st.selectbox("Selecione a Competição B:", all_tournaments, index=min(1, len(all_tournaments)-1), key="val_b")

    # Filtrar dados para A e B
    m_a, s_a = filter_dataset_by_preset(df_matches, df_shots, type_a, val_a)
    m_b, s_b = filter_dataset_by_preset(df_matches, df_shots, type_b, val_b)

    if m_a.empty or m_b.empty:
        st.warning("Não há partidas suficientes para os filtros selecionados.")
        return

    prof_a = compute_profile_metrics(m_a, s_a)
    prof_b = compute_profile_metrics(m_b, s_b)

    # 1. Cards Comparativos com Deltas
    st.markdown("---")
    st.markdown(f"#### 📊 Comparativo Direto: **{val_a}** vs. **{val_b}**")

    c1, c2, c3, c4 = st.columns(4)
    delta_xg90 = prof_b["xg_p90"] - prof_a["xg_p90"]
    delta_vol = prof_b["shots_p90"] - prof_a["shots_p90"]
    delta_qual = prof_b["xg_p_shot"] - prof_a["xg_p_shot"]
    delta_g90 = prof_b["goals_p90"] - prof_a["goals_p90"]

    c1.metric("xG / 90 min", f"{prof_b['xg_p90']:.2f}", f"{delta_xg90:+.2f} vs {val_a}")
    c2.metric("Chutes / 90 min", f"{prof_b['shots_p90']:.1f}", f"{delta_vol:+.1f} vs {val_a}")
    c3.metric("Qualidade (xG/Chute)", f"{prof_b['xg_p_shot']:.3f}", f"{delta_qual:+.3f} vs {val_a}")
    c4.metric("Gols / 90 min", f"{prof_b['goals_p90']:.2f}", f"{delta_g90:+.2f} vs {val_a}")

    c5, c6, c7, c8 = st.columns(4)
    delta_ft = prof_b["avg_field_tilt"] - prof_a["avg_field_tilt"]
    delta_tbox = prof_b["avg_touches_box"] - prof_a["avg_touches_box"]
    delta_cross = prof_b["avg_crosses"] - prof_a["avg_crosses"]
    delta_poss = prof_b["avg_possession"] - prof_a["avg_possession"]

    c5.metric("Field Tilt (% Terço Final)", f"{prof_b['avg_field_tilt']:.1f}%", f"{delta_ft:+.1f}% vs {val_a}")
    c6.metric("Toques na Área / Jogo", f"{prof_b['avg_touches_box']:.1f}", f"{delta_tbox:+.1f} vs {val_a}")
    c7.metric("Cruzamentos / Jogo", f"{prof_b['avg_crosses']:.1f}", f"{delta_cross:+.1f} vs {val_a}")
    c8.metric("Posse de Bola", f"{prof_b['avg_possession']:.1f}%", f"{delta_poss:+.1f}% vs {val_a}")

    st.markdown("---")

    # 2. Gráfico Radar Tático Comparativo
    c_rad, c_wf = st.columns([1, 1])

    with c_rad:
        st.markdown("#### 🕸️ Radar Tático Multidimensional (8 Eixos)")
        categories = [
            "Volume (Chutes/90)",
            "Qualidade (xG/Chute)",
            "Field Tilt (% Ataque)",
            "Toques na Área",
            "Proximidade (1/Dist)",
            "Jogo Aberto (% xG)",
            "Grandes Chances (%)",
            "Conversão (%)"
        ]

        # Normalização relativa para escala 0 a 100
        val_radar_a = [
            np.clip(prof_a["shots_p90"] / 20.0 * 100, 10, 100),
            np.clip(prof_a["xg_p_shot"] / 0.15 * 100, 10, 100),
            np.clip(prof_a["avg_field_tilt"], 10, 100),
            np.clip(prof_a["avg_touches_box"] / 30.0 * 100, 10, 100),
            np.clip((30.0 - prof_a["avg_dist"]) / 18.0 * 100, 10, 100),
            np.clip(prof_a["pct_open_play"], 10, 100),
            np.clip(prof_a["pct_high_danger"] * 4.0, 10, 100),
            np.clip(prof_a["conv_pct"] * 5.0, 10, 100)
        ]
        val_radar_b = [
            np.clip(prof_b["shots_p90"] / 20.0 * 100, 10, 100),
            np.clip(prof_b["xg_p_shot"] / 0.15 * 100, 10, 100),
            np.clip(prof_b["avg_field_tilt"], 10, 100),
            np.clip(prof_b["avg_touches_box"] / 30.0 * 100, 10, 100),
            np.clip((30.0 - prof_b["avg_dist"]) / 18.0 * 100, 10, 100),
            np.clip(prof_b["pct_open_play"], 10, 100),
            np.clip(prof_b["pct_high_danger"] * 4.0, 10, 100),
            np.clip(prof_b["conv_pct"] * 5.0, 10, 100)
        ]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=val_radar_a + [val_radar_a[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=f"A: {val_a}",
            line_color="#00BFFF",
            fillcolor="rgba(0, 191, 255, 0.25)"
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=val_radar_b + [val_radar_b[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=f"B: {val_b}",
            line_color="#00FF87",
            fillcolor="rgba(0, 255, 135, 0.25)"
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=False, range=[0, 100]),
                bgcolor="#111625"
            ),
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with c_wf:
        st.markdown("#### 🌊 Decomposição Fatorial do Saldo (A ➔ B)")
        mean_q = (prof_a["xg_p_shot"] + prof_b["xg_p_shot"]) / 2.0
        mean_v = (prof_a["shots_p90"] + prof_b["shots_p90"]) / 2.0
        eff_vol = delta_vol * mean_q
        eff_qual = mean_v * delta_qual

        fig_wf_comp = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=[f"xG/90 ({val_a})", "Efeito Volume", "Efeito Qualidade", f"xG/90 ({val_b})"],
            textposition="outside",
            text=[f"{prof_a['xg_p90']:.2f}", f"{eff_vol:+.2f}", f"{eff_qual:+.2f}", f"{prof_b['xg_p90']:.2f}"],
            y=[prof_a["xg_p90"], eff_vol, eff_qual, prof_b["xg_p90"]],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#FF4B4B"}},
            increasing={"marker": {"color": "#00FF87"}},
            totals={"marker": {"color": "#00BFFF"}}
        ))
        fig_wf_comp.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title="xG / 90 minutos"
        )
        st.plotly_chart(fig_wf_comp, use_container_width=True)

    # 3. Mapas Lado a Lado
    st.markdown("---")
    st.markdown("#### 🗺️ Mapas de Calor Espaciais Comparativos (KDE)")
    c_m1, c_m2 = st.columns([1, 1])

    pal_sa = s_a[s_a["is_palmeiras"] == True]
    pal_sb = s_b[s_b["is_palmeiras"] == True]

    with c_m1:
        fig_map_a = plot_density_shotmap(pal_sa, title=f"Densidade: {val_a}")
        st.plotly_chart(fig_map_a, use_container_width=True)

    with c_m2:
        fig_map_b = plot_density_shotmap(pal_sb, title=f"Densidade: {val_b}")
        st.plotly_chart(fig_map_b, use_container_width=True)

    # 4. Guia Metodológico
    with st.expander("📖 Guia Tático e Metodológico: O que o Modo Comparação responde e como interpretar", expanded=False):
        st.markdown(r"""
        ### 🎯 Qual pergunta queremos responder?
        1. **"O Palmeiras de 2026 é melhor ou pior que o de 2025?"** Avaliamos se o xG/90 subiu porque o time cria chances mais claras ou apenas porque chuta desesperadamente de longe.
        2. **"Houve queda de intensidade entre o 1º e o 2º Turno do Brasileirão?"** Identificamos se o time perdeu presença na área adversária (Toques na Área e Field Tilt) ou se foi mera oscilação de pontaria na conversão de gols.
        3. **"Qual é a diferença da postura no Brasileirão vs. Libertadores?"** Verificamos se em copas o time é mais reativo e vertical (menos posse, mas contra-ataques de alto xG/chute).

        ---

        ### 📊 Detalhamento das Dimensões do Radar Tático (8 Eixos)
        * **Volume (Chutes/90):** Quantidade bruta de tentativas por partida.
        * **Qualidade (xG/Chute):** Perigo intrínseco de cada finalização (seleção de arremate).
        * **Field Tilt (% Posse no Terço Final):** Mede o domínio territorial. Valores acima de 55% comprovam que o time acampa no campo adversário.
        * **Toques na Área / Jogo:** Frequência de infiltrações no miolo defensivo rival.
        * **Proximidade (1/Distância):** Quanto menor a distância média dos chutes até o gol, maior a pontuação no radar.
        * **Jogo Aberto (% xG):** Dependência de posse trabalhada versus bola parada.
        * **Grandes Chances (%):** Proporção de chutes com xG $\ge 0.30$.
        * **Conversão (%):** Eficiência clínica em transformar chutes em gols reais.

        ---

        ### ⚡ O Mito Desmontado vs. A Realidade Tática
        * **O Mito:** *"Se o time marcou menos gols no 2º turno, o trabalho do treinador piorou."*
        * **A Realidade:** Se o xG/90 e o Field Tilt se mantiveram estáveis (ou até subiram), a queda no número de gols decorre de variância de finalização (goleiros adversários em dias inspirados ou bolas na trave). O processo tático continua sólido; o resultado pontual engana o torcedor e a imprensa.
        """)
