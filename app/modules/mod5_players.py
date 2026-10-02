"""
Módulo 5: Raio-X por Jogador & Eficiência de Finalização.
"""

import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

from src.analytics.player_metrics import calculate_player_summary
from src.visualization.pitch_plotly import plot_interactive_shotmap
from src.visualization.pitch_mplsoccer import create_mplsoccer_shotmap

def render_players_tab(df_shots: pd.DataFrame, df_matches: pd.DataFrame):
    st.markdown("### 🎯 Módulo 5: Raio-X por Jogador & Eficiência de Finalização")

    st.info(
        "💡 **Eleve o Debate:** Atacantes passam por fases de 'seca' ou 'fase iluminada'. "
        "A métrica $G - xG$ (Gols Reais menos Gols Esperados) separa o que é **habilidade de finalização sustentável** "
        "do que é mera **variância estatística (sorte/azar temporário)**. "
        "Além disso, o xG por finalização mostra se o atleta se posiciona em zonas nobres ou finaliza no desespero."
    )

    pal_shots = df_shots[df_shots["is_palmeiras"] == True].copy()
    if pal_shots.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    # Tabela resumo de jogadores
    player_summary = calculate_player_summary(df_shots, min_shots=3)
    if player_summary.empty:
        st.warning("Poucos chutes registrados para gerar o ranking de jogadores.")
        return

    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("#### Matriz de Eficiência: xG Acumulado vs. Conversão (G - xG)")
        fig_scatter = px.scatter(
            player_summary,
            x="total_xg",
            y="xg_overperformance",
            size="total_shots",
            color="player_position",
            text="player_name",
            hover_data=["total_goals", "total_shots", "xg_per_shot", "avg_distance"],
            labels={
                "total_xg": "xG Total Acumulado (Volume de Chances)",
                "xg_overperformance": "Saldo de Conversão (Gols - xG)",
                "player_position": "Posição"
            },
            template="plotly_dark"
        )
        fig_scatter.update_traces(textposition="top center")
        fig_scatter.add_hline(y=0, line_dash="dash", line_color="white", annotation_text="xG Neutro (Esperado)")
        fig_scatter.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with c2:
        st.markdown("#### Top 8 Finalizadores em xG Acumulado")
        top8 = player_summary.head(8).sort_values(by="total_xg", ascending=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=top8["player_name"],
            x=top8["total_xg"],
            name="xG Acumulado",
            orientation="h",
            marker_color="#00BFFF",
            text=top8["total_xg"],
            textposition="auto"
        ))
        fig_bar.add_trace(go.Bar(
            y=top8["player_name"],
            x=top8["total_goals"],
            name="Gols Reais",
            orientation="h",
            marker_color="#00FF87",
            text=top8["total_goals"],
            textposition="auto"
        ))
        fig_bar.update_layout(
            barmode="group",
            template="plotly_dark",
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("#### 📋 Tabela Completa de Finalizadores do Palmeiras")
    display_players = player_summary[[
        "player_name", "player_position", "matches_with_shot", "total_shots",
        "total_goals", "total_xg", "xg_overperformance", "xg_per_shot", "conversion_pct",
        "pct_high_danger", "avg_distance"
    ]].rename(columns={
        "player_name": "Jogador",
        "player_position": "Posição",
        "matches_with_shot": "Jogos com Chute",
        "total_shots": "Finalizações",
        "total_goals": "Gols",
        "total_xg": "xG Total",
        "xg_overperformance": "G - xG (Saldo)",
        "xg_per_shot": "xG / Chute",
        "conversion_pct": "Conversão (%)",
        "pct_high_danger": "Grandes Chances (%)",
        "avg_distance": "Distância Média (m)"
    })
    st.dataframe(display_players, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 3. Raio-X Individual do Atleta
    st.markdown("#### 👤 Raio-X Individual e Exportação de Card Editorial")
    
    player_list = list(player_summary["player_name"].unique())
    selected_player = st.selectbox("Selecione o jogador para dissecar:", player_list)

    player_shots = pal_shots[pal_shots["player_name"] == selected_player]
    p_info = player_summary[player_summary["player_name"] == selected_player].iloc[0]

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Finalizações", f"{p_info['total_shots']}")
    k2.metric("Gols Marcados", f"{p_info['total_goals']}")
    k3.metric("xG Acumulado", f"{p_info['total_xg']:.2f}")
    k4.metric("Saldo (G - xG)", f"{p_info['xg_overperformance']:+.2f}")
    k5.metric("Qualidade Média", f"{p_info['xg_per_shot']:.3f}")
    k6.metric("Distância Média", f"{p_info['avg_distance']:.1f} m")

    c_plot, c_card = st.columns([1.2, 0.8])

    with c_plot:
        st.markdown(f"##### Campo Interativo: {selected_player}")
        fig_player_pitch = plot_interactive_shotmap(
            player_shots,
            title=f"Mapa de Chutes: {selected_player}"
        )
        st.plotly_chart(fig_player_pitch, use_container_width=True)

    with c_card:
        st.markdown("##### Card Editorial em Mplsoccer (Pronto para Postar)")
        fig_mpl = create_mplsoccer_shotmap(
            player_shots,
            title=f"{selected_player} - Finalizações",
            subtitle=f"Palmeiras | Gols: {p_info['total_goals']} | xG: {p_info['total_xg']:.2f} | Saldo: {p_info['xg_overperformance']:+.2f}"
        )
        st.pyplot(fig_mpl)

        # Botão de download do PNG do card
        buf = io.BytesIO()
        fig_mpl.savefig(buf, format="png", dpi=300, bbox_inches="tight", facecolor=fig_mpl.get_facecolor())
        buf.seek(0)
        
        st.download_button(
            label=f"📥 Baixar Card HD ({selected_player}.png)",
            data=buf,
            file_name=f"card_xg_{selected_player.lower().replace(' ', '_')}.png",
            mime="image/png",
            use_container_width=True
        )
        plt.close(fig_mpl)

    # 4. Mapa de Calor Real de Toques do Jogador na Partida
    st.markdown("---")
    st.markdown(f"#### 🗺️ Mapa de Calor Real de Toques (Heatmap de Atuação: {selected_player})")
    
    player_match_ids = player_shots["match_id"].unique()
    player_matches = df_matches[df_matches["match_id"].isin(player_match_ids)].sort_values(by="date", ascending=False)
    
    if not player_matches.empty:
        c_hm1, c_hm2 = st.columns([1.2, 0.8])
        with c_hm1:
            match_opts = {
                f"{row['date']} | {row['home_team']} {row['home_score']}x{row['away_score']} {row['away_team']} ({row['tournament']})": row["match_id"]
                for _, row in player_matches.iterrows()
            }
            sel_m_label = st.selectbox("Selecione o confronto para visualizar onde o jogador tocou na bola:", list(match_opts.keys()), key="p_hm_match")
            sel_m_id = match_opts[sel_m_label]
            m_row = player_matches[player_matches["match_id"] == sel_m_id].iloc[0]

        from src.ingestion.sofascore_client import SofaScoreClient
        from src.visualization.player_touch_heatmap import plot_player_touch_heatmap
        client = SofaScoreClient()
        hm_data = client.get_player_heatmap(sel_m_id, int(p_info["player_id"]), season_year=str(m_row["season"]))
        
        if hm_data and "heatmap" in hm_data and hm_data["heatmap"]:
            fig_hm = plot_player_touch_heatmap(
                hm_data["heatmap"],
                player_name=selected_player,
                match_title=f"{m_row['home_team']} x {m_row['away_team']} ({m_row['tournament']})"
            )
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info(f"Dados de toques na bola não disponíveis para {selected_player} nesta partida específica.")
    else:
        st.info("Nenhuma partida com finalizações registradas para este atleta no filtro atual.")

    # 5. Guia Metodológico
    with st.expander("📖 Guia Tático: O que esta tela responde e como interpretar"):
        st.markdown("""
        **1. Qual pergunta queremos responder?**
        - O atacante está em má fase técnica ou apenas enfrentando uma oscilação natural de variância probabilística?
        - Quem são os geradores de volume (chutam muito) versus finalizadores de alta eficiência (convertem chances difíceis)?
        - Onde o jogador realmente atua com a bola no campo (heatmap de toques)?
        
        **2. Dicionário de Variáveis e Dados:**
        - **xG Acumulado:** Soma da probabilidade de gol de todas as finalizações tentadas pelo atleta.
        - **Saldo de Conversão ($G - xG$):** Gols Reais menos Gols Esperados.
          - Valor $> 0$: O jogador marcou mais gols do que a média dos atletas marcaria a partir daquelas posições (sobre-desempenho).
          - Valor $< 0$: O jogador marcou menos gols do que o esperado (sub-desempenho ou azar pontual).
        - **xG por Chute:** Mede a inteligência de posicionamento do atacante. Atacantes que só chutam dentro da pequena/grande área têm $xG/\text{chute} > 0.15$; chutadores de longe têm $< 0.06$.
        - **Heatmap de Toques:** Densidade 2D em campo regulamentar de 105m x 68m registrando onde o jogador participou com a bola.
        
        **3. O Mito Desmontado:**
        - Um atacante que passa 4 jogos sem marcar, mas acumulou 2.5 de xG, está jogando bem e se posicionando certo — a bola voltará a entrar por regressão à média. Já um jogador que marcou 3 gols em 3 chutes de 0.04 xG não é necessariamente um gênio da finalização, e seu rendimento deve cair.
        """)
