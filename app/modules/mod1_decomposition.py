"""
Módulo 1: Decomposição Volume x Qualidade (Shots/90 * xG/Shot).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.analytics.decomposition import calculate_volume_quality_metrics
from src.visualization.pitch_plotly import plot_interactive_shotmap

def render_decomposition_tab(df_shots: pd.DataFrame, df_matches: pd.DataFrame):
    st.markdown("### 📊 Módulo 1: Decomposição Volume vs. Qualidade")
    
    st.info(
        "💡 **Eleve o Debate:** Comparar apenas o 'xG total' esconde a real dinâmica do ataque. "
        "Uma equipe com 2.0 de xG pode ter produzido **20 chutes de 0.10** (bombardeio de média distância) "
        "ou **3 chances claríssimas de 0.67** (ataque cirúrgico). A decomposição formal: "
        r"$\text{xG/90} = \text{Shots/90} \times \text{xG/shot}$ revela se o time cria em volume ou em alta definição."
    )

    pal_shots = df_shots[df_shots["is_palmeiras"] == True].copy()
    if pal_shots.empty or df_matches.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    # Métricas Gerais em Cards
    total_matches = df_matches["match_id"].nunique()
    total_shots = len(pal_shots)
    total_xg = pal_shots["xg"].sum()
    total_goals = pal_shots["is_goal"].sum()
    
    shots_p90 = total_shots / total_matches if total_matches > 0 else 0
    xg_p_shot = total_xg / total_shots if total_shots > 0 else 0
    xg_p90 = total_xg / total_matches if total_matches > 0 else 0
    goals_p90 = total_goals / total_matches if total_matches > 0 else 0
    conv_rate = (total_goals / total_shots * 100) if total_shots > 0 else 0
    avg_dist = pal_shots["distance_meters"].mean()
    avg_ang = pal_shots["angle_degrees"].mean()

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Chutes / 90 min", f"{shots_p90:.1f}")
    col2.metric("Qualidade (xG / Chute)", f"{xg_p_shot:.3f}")
    col3.metric("xG / 90 min", f"{xg_p90:.2f}")
    col4.metric("Gols / 90 min", f"{goals_p90:.2f}")
    col5.metric("Taxa de Conversão", f"{conv_rate:.1f}%")
    col6.metric("Distância Média", f"{avg_dist:.1f} m")

    st.markdown("---")

    # Decomposição por Competição ou Temporada
    group_col = "tournament" if df_matches["tournament"].nunique() > 1 else "season"
    metrics_table = calculate_volume_quality_metrics(df_shots, df_matches, group_by_col=group_col)

    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown(f"#### Relação Volume x Qualidade por {group_col.capitalize()}")
        fig_scatter = px.scatter(
            metrics_table,
            x="shots_per_90",
            y="xg_per_shot",
            size="xg_per_90",
            color=group_col,
            text=group_col,
            hover_data=["total_matches", "goals_per_90", "conversion_rate", "avg_distance"],
            labels={
                "shots_per_90": "Volume (Finalizações por 90 min)",
                "xg_per_shot": "Qualidade Média (xG por Chute)",
                "xg_per_90": "xG / 90 min"
            },
            template="plotly_dark"
        )
        fig_scatter.update_traces(textposition="top center", marker=dict(opacity=0.85, line=dict(width=1, color="white")))
        # Linhas de média
        fig_scatter.add_vline(x=shots_p90, line_dash="dash", line_color="#718096", annotation_text="Média Volume", annotation_position="bottom right")
        fig_scatter.add_hline(y=xg_p_shot, line_dash="dash", line_color="#718096", annotation_text="Média Qualidade", annotation_position="top left")
        fig_scatter.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with c_right:
        st.markdown("#### Perfil de Perigo das Finalizações (% do Total de Chutes)")
        danger_counts = pal_shots["xg_danger"].value_counts(normalize=True).reset_index()
        danger_counts.columns = ["Faixa de Perigo", "Proporção"]
        danger_counts["Percentual"] = (danger_counts["Proporção"] * 100).round(1)

        color_danger = {
            "Alta (>=0.30)": "#00FF87",
            "Média (0.10 a 0.29)": "#00BFFF",
            "Baixa (0.04 a 0.09)": "#FFA500",
            "Especulativa (<0.04)": "#FF4B4B"
        }
        fig_bar = px.bar(
            danger_counts,
            x="Faixa de Perigo",
            y="Percentual",
            color="Faixa de Perigo",
            color_discrete_map=color_danger,
            text=danger_counts["Percentual"].apply(lambda v: f"{v}%"),
            template="plotly_dark"
        )
        fig_bar.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tabela detalhada
    st.markdown("#### 📋 Tabela Comparativa Consolidada")
    display_df = metrics_table[[
        group_col, "total_matches", "total_shots", "shots_per_90", "xg_per_shot",
        "xg_per_90", "goals_per_90", "conversion_rate", "pct_high_danger", "avg_distance"
    ]].rename(columns={
        group_col: "Agrupamento",
        "total_matches": "Partidas",
        "total_shots": "Chutes",
        "shots_per_90": "Chutes/90",
        "xg_per_shot": "xG/Chute",
        "xg_per_90": "xG/90",
        "goals_per_90": "Gols/90",
        "conversion_rate": "Conversão (%)",
        "pct_high_danger": "Grandes Chances (%)",
        "avg_distance": "Dist. Média (m)"
    })
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    with st.expander("📖 Guia Tático: O que esta tela responde e como interpretar"):
        st.markdown(r"""
        **1. Qual pergunta queremos responder?**
        - O ataque do Palmeiras é prolífico por volume bruto (bombardeio de chutes) ou por precisão posicional (chances claríssimas de alta probabilidade)?
        - O time está chutando de perto ou recorrendo ao desespero de chutes de longa distância?
        
        **2. Dicionário de Variáveis e Dados:**
        - **xG/90:** Gols esperados normalizados por 90 minutos de jogo ($\text{xG Total} / \text{Partidas}$).
        - **Chutes/90 (Volume):** Total de finalizações tentadas a cada 90 minutos.
        - **xG/Chute (Qualidade Média):** Perigo médio de cada tentativa ($\text{xG Total} / \text{Chutes Totais}$). Valores acima de $0.12$ indicam excelente seleção de finalização; valores abaixo de $0.07$ apontam precipitação.
        - **Distância Média (m):** Distância euclidiana das coordenadas do chute até a linha central do gol em metros ($d = \sqrt{x^2 + y^2}$).
        - **Faixas de Perigo:**
          - *Alta ($\ge 0.30$):* Grandes chances (cara a cara com o goleiro, pequenas áreas).
          - *Média ($0.10$ a $0.29$):* Chutes de dentro da grande área com ângulo razoável.
          - *Baixa ($0.04$ a $0.09$):* Chutes marcados na entrada da área.
          - *Especulativa ($< 0.04$):* Chutes de longe ou com ângulo fechado na linha de fundo.
        
        **3. O Mito Desmontado:**
        - Comemorar um xG alto sem decompor em $Shots/90 \times xG/shot$ é enganoso. Uma equipe com 20 chutes de $0.05$ (1.0 de xG) tem muito menos probabilidade de marcar do que uma equipe com 2 chutes de $0.50$ (mesmo 1.0 de xG), porque a probabilidade de converter pelo menos um gol é de $64\%$ no segundo caso contra apenas $63\%$ no primeiro, além de gerar menos contra-ataques ao adversário.
        """)
