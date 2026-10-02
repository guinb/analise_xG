"""
Módulo 2: Efeito Game State & O Mito do Placar.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.visualization.pitch_plotly import plot_interactive_shotmap

def render_game_state_tab(df_shots: pd.DataFrame, df_matches: pd.DataFrame):
    st.markdown("### ⏱️ Módulo 2: Efeito Game State & O Mito do Placar")

    st.info(
        "💡 **Eleve o Debate:** Uma das maiores fontes de análise equivocada na imprensa é comparar o xG sem considerar o placar momentâneo. "
        "Quando o Palmeiras abre 2 a 0, a equipe adota um bloco médio-baixo, controla espaços e concede a posse. "
        "O adversário, no desespero, passa a acumular finalizações de longe e inflar seu xG. "
        "Aqui normalizamos a taxa de xG **pelos minutos reais jogados em cada estado de jogo**."
    )

    pal_shots = df_shots[df_shots["is_palmeiras"] == True].copy()
    opp_shots = df_shots[df_shots["is_palmeiras"] == False].copy()

    if pal_shots.empty or df_matches.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    # Total de minutos jogados em cada estado
    total_min_win = df_matches["minutes_winning"].sum()
    total_min_draw = df_matches["minutes_drawing"].sum()
    total_min_loss = df_matches["minutes_losing"].sum()
    total_min_all = total_min_win + total_min_draw + total_min_loss

    pct_win = (total_min_win / total_min_all * 100) if total_min_all > 0 else 0
    pct_draw = (total_min_draw / total_min_all * 100) if total_min_all > 0 else 0
    pct_loss = (total_min_loss / total_min_all * 100) if total_min_all > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Tempo Vencendo", f"{total_min_win:.0f} min", f"{pct_win:.1f}% do tempo")
    col2.metric("Tempo Empatando", f"{total_min_draw:.0f} min", f"{pct_draw:.1f}% do tempo")
    col3.metric("Tempo Perdendo", f"{total_min_loss:.0f} min", f"{pct_loss:.1f}% do tempo")

    st.markdown("---")

    # Calcular xG criado e concedido por estado
    states = ["Vencendo", "Empatando", "Perdendo"]
    state_metrics = []

    for st_name in states:
        p_sub = pal_shots[pal_shots["game_state"] == st_name]
        o_sub = opp_shots[opp_shots["game_state"] == st_name]
        
        mins = total_min_win if st_name == "Vencendo" else (total_min_draw if st_name == "Empatando" else total_min_loss)
        mins_90 = mins / 90.0 if mins > 0 else 0.001

        p_xg = p_sub["xg"].sum()
        o_xg = o_sub["xg"].sum()
        p_shots = len(p_sub)
        o_shots = len(o_sub)

        state_metrics.append({
            "Estado": st_name,
            "Minutos": int(mins),
            "Chutes Palmeiras/90": round(p_shots / mins_90, 2),
            "xG Criado/90": round(p_xg / mins_90, 2),
            "Chutes Sofridos/90": round(o_shots / mins_90, 2),
            "xG Sofrido/90": round(o_xg / mins_90, 2),
            "Saldo xG/90 (xGD/90)": round((p_xg - o_xg) / mins_90, 2),
            "xG/Chute Palmeiras": round(p_xg / p_shots, 3) if p_shots > 0 else 0,
            "xG/Chute Sofrido": round(o_xg / o_shots, 3) if o_shots > 0 else 0
        })

    df_state = pd.DataFrame(state_metrics)

    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("#### Produção vs Concessão de xG / 90 min por Estado")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=df_state["Estado"],
            y=df_state["xG Criado/90"],
            name="Palmeiras (xG Criado / 90)",
            marker_color="#00FF87",
            text=df_state["xG Criado/90"],
            textposition="auto"
        ))
        fig_bar.add_trace(go.Bar(
            x=df_state["Estado"],
            y=df_state["xG Sofrido/90"],
            name="Adversários (xG Concedido / 90)",
            marker_color="#FF4B4B",
            text=df_state["xG Sofrido/90"],
            textposition="auto"
        ))
        fig_bar.update_layout(
            barmode="group",
            template="plotly_dark",
            height=400,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.markdown("#### Saldo Líquido de xG por 90 min (xGD / 90)")
        colors = ["#00FF87" if v >= 0 else "#FF4B4B" for v in df_state["Saldo xG/90 (xGD/90)"]]
        fig_diff = px.bar(
            df_state,
            x="Estado",
            y="Saldo xG/90 (xGD/90)",
            text="Saldo xG/90 (xGD/90)",
            template="plotly_dark"
        )
        fig_diff.update_traces(marker_color=colors, textposition="outside")
        fig_diff.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_diff, use_container_width=True)

    st.markdown("#### 📋 Matriz Tática de Game State")
    st.dataframe(df_state, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### 🗺️ Análise Espacial Filtrada por Estado do Jogo")
    c_st1, c_st2 = st.columns([1, 1])
    with c_st1:
        selected_state = st.radio("Selecione o estado para visualizar no campo:", ["Todos", "Empatando", "Vencendo", "Perdendo"], horizontal=True)
    with c_st2:
        view_mode = st.radio("Modo de Visualização:", ["🔥 Mapa de Calor (Densidade)", "📐 Zonas Táticas Regulamentares", "📍 Finalizações Discretas"], horizontal=True)
    
    if selected_state == "Todos":
        shots_to_plot = pal_shots
    else:
        shots_to_plot = pal_shots[pal_shots["game_state"] == selected_state]

    from src.visualization.pitch_density import plot_density_shotmap, plot_tactical_zones_pitch

    if view_mode == "🔥 Mapa de Calor (Densidade)":
        fig_pitch = plot_density_shotmap(
            shots_to_plot,
            title=f"Densidade de Finalizações do Palmeiras - Estado: {selected_state}"
        )
    elif view_mode == "📐 Zonas Táticas Regulamentares":
        fig_pitch = plot_tactical_zones_pitch(
            shots_to_plot,
            title=f"xG por Zona Tática - Estado: {selected_state} ({len(shots_to_plot)} chutes)"
        )
    else:
        filter_scope = st.selectbox("Filtro de pontos:", ["Apenas Gols e Grandes Chances (xG >= 0.15)", "Apenas Gols", "Todas as Finalizações (com opacidade suave)"])
        if filter_scope == "Apenas Gols e Grandes Chances (xG >= 0.15)":
            pts = shots_to_plot[(shots_to_plot["is_goal"] == True) | (shots_to_plot["xg"] >= 0.15)]
        elif filter_scope == "Apenas Gols":
            pts = shots_to_plot[shots_to_plot["is_goal"] == True]
        else:
            pts = shots_to_plot
            
        fig_pitch = plot_interactive_shotmap(
            pts,
            title=f"Finalizações - Estado: {selected_state} ({len(pts)} chutes exibidos)"
        )

    st.plotly_chart(fig_pitch, use_container_width=True)

    with st.expander("📖 Guia Tático: O que esta tela responde e como interpretar"):
        st.markdown(r"""
        **1. Qual pergunta queremos responder?**
        - O Palmeiras produz mais ou menos quando está em desvantagem versus em vantagem no placar?
        - O volume de chutes sofridos decorre de falhas defensivas ou de um recuo estratégico natural para administrar o resultado?
        
        **2. Dicionário de Variáveis e Dados:**
        - **Game State (Estado do Placar):** Calculado para cada segundo da partida a partir da linha do tempo oficial de gols da API.
          - *Vencendo:* Diferença de gols a favor ($\text{Gols Palmeiras} - \text{Gols Adversário} \ge 1$).
          - *Empatando:* Diferença de gols igual a 0.
          - *Perdendo:* Diferença de gols negativa ($\le -1$).
        - **Minutos Reais por Estado:** Tempo exato (em minutos) que a equipe permaneceu em cada condição de placar.
        - **xG Criado / 90 min no Estado:** $\frac{\sum \text{xG gerado no estado}}{\text{Minutos no estado}} \times 90$.
        - **xG Sofrido / 90 min no Estado:** $\frac{\sum \text{xG concedido no estado}}{\text{Minutos no estado}} \times 90$.
        - **Saldo xG/90 (xGD/90):** $\text{xG Criado/90} - \text{xG Sofrido/90}$.
        
        **3. O Mito Desmontado:**
        - O mito do "domínio enganoso": Um time que sai na frente aos 15 minutos passa 75 minutos vencendo. O adversário passa a finalizar de qualquer lugar e acumula xG alto no desespero. Sem normalizar por minutos de Game State, a imprensa rotula falsamente que o adversário "merecia empatar" ou que o Palmeiras "foi dominado".
        """)
