"""
Módulo 3: Anatomia da Criação (Fases do Jogo & Situação).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.visualization.pitch_plotly import plot_interactive_shotmap

def render_creation_phase_tab(df_shots: pd.DataFrame, df_matches: pd.DataFrame):
    st.markdown("### 🧩 Módulo 3: Anatomia da Criação (Fases do Jogo)")

    with st.expander("📖 Guia Tático e Metodológico: O que esta tela responde e como interpretar", expanded=False):
        st.markdown(
            """
            ### 🎯 Qual pergunta queremos responder?
            1. **"O time é excessivamente dependente de bola parada ou sustenta perigo em jogo aberto?"**
            2. **"Qual é a mecânica de ataque mais letal?"** Comparando o rendimento qualitativo de contra-ataques, bolas paradas e ataque posicional.
            3. **"Onde está a ilusão do volume?"** Muitas vezes uma equipe finaliza 15 vezes em jogo aberto mas com chances fracas (xG 0.05) e gera mais perigo real em 4 escanteios bem trabalhados.

            ---

            ### 📊 Detalhamento das Variáveis e Dados
            * **Fase / Situação (`situation`):**
              * `regular` (Jogo Aberto): Posse contínua e passes em movimento antes do chute.
              * `corner` (Escanteio): Primeira ou segunda jogada imediatamente derivada da cobrança de córner.
              * `free-kick` (Falta): Faltas diretas para o gol ou cruzamentos ensaiados em cobrança de infração.
              * `fast-break` (Contra-Ataque): Transição acelerada contra a defesa adversária desorganizada.
              * `penalty` (Pênalti): Finalização padrão da marca da cal (xG padronizado ~0.76 - 0.79).
            * **Share Volume (%) vs Share xG (%):**
              * Se um time tem `Share Volume = 70%` em jogo aberto mas apenas `Share xG = 50%`, sua criação em bola rolando é ineficiente (chutes descalibrados de longe).
              * Se em escanteios o time tem `Share Volume = 20%` e `Share xG = 38%`, sua bola parada é um trunfo gerador de perigo de elite.
            * **xG por Finalização (`xG/chute`):** Qualidade média intrínseca de cada tipo de oportunidade. Contra-ataques e pênaltis costumam ter xG/chute muito superior a chutes de longa distância.

            ---

            ### ⚡ O Mito Desmontado vs. A Realidade Tática
            * **O Mito:** *"Time bom cria tudo em jogo aberto com 40 passes; fazer gol de escanteio é sorte ou demérito do rival."*
            * **A Realidade:** Na elite mundial (como Manchester City e Arsenal de Mikel Arteta), as bolas paradas ensaiadas representam mais de 30% da produção ofensiva de xG. Treinar bolas paradas com alto xG não é falta de repertório, é maximização matemática da eficiência espacial.
            """
        )

    pal_shots = df_shots[df_shots["is_palmeiras"] == True].copy()
    if pal_shots.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    # Agregação por Situação
    sit_agg = pal_shots.groupby("situation").agg(
        total_chutes=("shot_id", "count"),
        total_xg=("xg", "sum"),
        total_gols=("is_goal", "sum"),
        distancia_media=("distance_meters", "mean"),
        angulo_medio=("angle_degrees", "mean")
    ).reset_index()

    total_chutes_all = sit_agg["total_chutes"].sum()
    total_xg_all = sit_agg["total_xg"].sum()

    sit_agg["share_volume"] = (sit_agg["total_chutes"] / total_chutes_all * 100).round(1)
    sit_agg["share_xg"] = (sit_agg["total_xg"] / total_xg_all * 100).round(1)
    sit_agg["xg_por_chute"] = (sit_agg["total_xg"] / sit_agg["total_chutes"]).round(3)
    sit_agg["conversao_pct"] = ((sit_agg["total_gols"] / sit_agg["total_chutes"]) * 100).round(1)
    sit_agg["distancia_media"] = sit_agg["distancia_media"].round(1)
    sit_agg["total_xg"] = sit_agg["total_xg"].round(2)

    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("#### Participação no Volume de Chutes vs. Produção de xG")
        fig_pie = go.Figure()
        fig_pie.add_trace(go.Pie(
            labels=sit_agg["situation"],
            values=sit_agg["total_chutes"],
            name="Volume de Chutes",
            hole=0.45,
            domain=dict(x=[0, 0.48]),
            title="Volume (Chutes)"
        ))
        fig_pie.add_trace(go.Pie(
            labels=sit_agg["situation"],
            values=sit_agg["total_xg"],
            name="Qualidade xG",
            hole=0.45,
            domain=dict(x=[0.52, 1.0]),
            title="Produção (xG)"
        ))
        fig_pie.update_layout(
            template="plotly_dark",
            height=380,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.markdown("#### Qualidade Média da Oportunidade (xG / Chute) por Fase")
        fig_bar = px.bar(
            sit_agg.sort_values(by="xg_por_chute", ascending=True),
            x="xg_por_chute",
            y="situation",
            orientation="h",
            color="situation",
            text="xg_por_chute",
            template="plotly_dark",
            labels={"xg_por_chute": "xG Médio por Finalização", "situation": "Fase de Jogo"}
        )
        fig_bar.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("#### 📋 Detalhamento Numérico por Fase de Jogo")
    display_table = sit_agg.rename(columns={
        "situation": "Fase / Situação",
        "total_chutes": "Finalizações",
        "total_xg": "xG Total",
        "total_gols": "Gols Reais",
        "share_volume": "Share Volume (%)",
        "share_xg": "Share xG (%)",
        "xg_por_chute": "xG / Chute",
        "conversao_pct": "Conversão (%)",
        "distancia_media": "Distância Média (m)"
    })
    st.dataframe(display_table, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### 🗺️ Comparação Espacial de Criação")
    c_ph1, c_ph2 = st.columns([1, 1])
    with c_ph1:
        selected_sit = st.selectbox(
            "Selecione uma fase de jogo para inspecionar no campo:",
            ["Todas as Fases"] + list(sit_agg["situation"].unique())
        )
    with c_ph2:
        view_mode_ph = st.radio("Modo de Visualização:", ["🔥 Mapa de Calor (Densidade)", "📐 Zonas Táticas Regulamentares", "📍 Finalizações Discretas"], horizontal=True, key="view_mode_ph")

    if selected_sit == "Todas as Fases":
        subset_shots = pal_shots
    else:
        subset_shots = pal_shots[pal_shots["situation"] == selected_sit]

    from src.visualization.pitch_density import plot_density_shotmap, plot_tactical_zones_pitch

    if view_mode_ph == "🔥 Mapa de Calor (Densidade)":
        fig_sit_pitch = plot_density_shotmap(
            subset_shots,
            title=f"Densidade de Chutes - {selected_sit} ({len(subset_shots)} finalizações)"
        )
    elif view_mode_ph == "📐 Zonas Táticas Regulamentares":
        fig_sit_pitch = plot_tactical_zones_pitch(
            subset_shots,
            title=f"xG por Zona Tática - {selected_sit} ({len(subset_shots)} chutes)"
        )
    else:
        filter_ph = st.selectbox("Filtro de pontos:", ["Apenas Gols e Grandes Chances (xG >= 0.15)", "Apenas Gols", "Todas as Finalizações"], key="filter_ph")
        if filter_ph == "Apenas Gols e Grandes Chances (xG >= 0.15)":
            pts = subset_shots[(subset_shots["is_goal"] == True) | (subset_shots["xg"] >= 0.15)]
        elif filter_ph == "Apenas Gols":
            pts = subset_shots[subset_shots["is_goal"] == True]
        else:
            pts = subset_shots

        fig_sit_pitch = plot_interactive_shotmap(
            pts,
            title=f"Finalizações do Palmeiras - {selected_sit} ({len(pts)} chutes exibidos)"
        )
    st.plotly_chart(fig_sit_pitch, use_container_width=True)
