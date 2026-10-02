"""
Módulo 4: Simulação Monte Carlo & Variância Estatística (G - xG).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.analytics.monte_carlo import simulate_match_outcome, simulate_all_matches
from src.visualization.pitch_plotly import plot_interactive_shotmap

def render_simulation_tab(df_shots: pd.DataFrame, df_matches: pd.DataFrame):
    st.markdown("### 🎲 Módulo 4: Simulação Monte Carlo & Sorte / Variância")

    st.info(
        "💡 **Eleve o Debate:** O futebol é o esporte de maior aleatoriedade do mundo. "
        "Um time pode criar 2.8 de xG e perder de 1 a 0 em um chute desviado de 0.03 xG do adversário. "
        "A **Simulação Monte Carlo** executa 10.000 iterações de cada partida, simulando o resultado de cada finalização "
        "para estimar a probabilidade real de Vitória, Empate e Derrota, gerando os **Pontos Esperados (xPTS)**."
    )

    if df_matches.empty or df_shots.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    # 1. Tendência Estrutural: Rolling xGD (Saldo de xG móvel de 5 jogos)
    st.markdown("#### 📈 Tendência Estrutural: Média Móvel de Saldo de xG (xGD)")
    sorted_matches = df_matches.sort_values(by="date").copy()
    sorted_matches["xg_diff_rolling5"] = sorted_matches["xg_diff"].rolling(window=5, min_periods=1).mean()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        x=sorted_matches["date"],
        y=sorted_matches["xg_diff"],
        name="Saldo xG da Partida (xG Pró - xG Contra)",
        marker_color=["#00FF87" if v >= 0 else "#FF4B4B" for v in sorted_matches["xg_diff"]],
        opacity=0.45
    ))
    fig_trend.add_trace(go.Scatter(
        x=sorted_matches["date"],
        y=sorted_matches["xg_diff_rolling5"],
        name="Média Móvel (5 Partidas)",
        line=dict(color="#00BFFF", width=3)
    ))
    fig_trend.add_hline(y=0, line_dash="dash", line_color="white")
    fig_trend.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # 2. Simulador de Partida Individual
    st.markdown("#### 🔍 Simulador de Partida Específica (10.000 Iterações)")
    
    # Criar opções de seleção de partidas com xG
    xg_matches = df_matches[df_matches["has_xg"] == True].sort_values(by="date", ascending=False)
    if xg_matches.empty:
        st.warning("Nenhuma partida com xG disponível no filtro atual.")
        return

    match_options = {
        f"{row['date']} | {row['home_team']} {row['home_score']}x{row['away_score']} {row['away_team']} ({row['tournament']})": row["match_id"]
        for _, row in xg_matches.iterrows()
    }

    selected_match_label = st.selectbox("Selecione a partida para dissecar:", list(match_options.keys()))
    selected_match_id = match_options[selected_match_label]
    
    match_row = xg_matches[xg_matches["match_id"] == selected_match_id].iloc[0]
    match_shots = df_shots[df_shots["match_id"] == selected_match_id].sort_values(by="minute")

    pal_xgs = match_shots[match_shots["is_palmeiras"] == True]["xg"].values
    opp_xgs = match_shots[match_shots["is_palmeiras"] == False]["xg"].values

    sim = simulate_match_outcome(pal_xgs, opp_xgs, n_simulations=10000)

    # Exibição de cards de probabilidade
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("P(Vitória Palmeiras)", f"{sim['prob_win']}%")
    col2.metric("P(Empate)", f"{sim['prob_draw']}%")
    col3.metric("P(Derrota Palmeiras)", f"{sim['prob_loss']}%")
    col4.metric("Pontos Esperados (xPTS)", f"{sim['xpts']:.2f} pts")

    # Gráfico da linha do tempo minuto a minuto do xG acumulado
    st.markdown("#### ⏱️ Linha do Tempo de xG Acumulado (Minuto a Minuto)")
    
    timeline_rows = []
    cum_pal = 0.0
    cum_opp = 0.0
    timeline_rows.append({"minute": 0, "cum_palmeiras": 0.0, "cum_opponent": 0.0, "event": ""})

    for _, s in match_shots.iterrows():
        m = s["minute"]
        xg = s["xg"]
        is_g = s["is_goal"]
        if s["is_palmeiras"]:
            cum_pal += xg
            evt = f"GOL PAL ({s['player_name']})" if is_g else ""
        else:
            cum_opp += xg
            evt = f"GOL ADV ({s['player_name']})" if is_g else ""
        timeline_rows.append({"minute": m, "cum_palmeiras": cum_pal, "cum_opponent": cum_opp, "event": evt})

    timeline_rows.append({"minute": 95, "cum_palmeiras": cum_pal, "cum_opponent": cum_opp, "event": ""})
    df_timeline = pd.DataFrame(timeline_rows)

    fig_timeline = go.Figure()
    fig_timeline.add_trace(go.Scatter(
        x=df_timeline["minute"], y=df_timeline["cum_palmeiras"],
        name=f"Palmeiras (xG Final: {cum_pal:.2f})",
        line=dict(color="#00FF87", width=3, shape="hv")
    ))
    fig_timeline.add_trace(go.Scatter(
        x=df_timeline["minute"], y=df_timeline["cum_opponent"],
        name=f"{match_row['opponent_name']} (xG Final: {cum_opp:.2f})",
        line=dict(color="#FF4B4B", width=3, shape="hv")
    ))

    # Marcar os gols com pontos luminosos diretamente nas linhas (sem poluição de caixas de texto colidindo)
    pal_goals = match_shots[(match_shots["is_palmeiras"] == True) & (match_shots["is_goal"] == True)]
    opp_goals = match_shots[(match_shots["is_palmeiras"] == False) & (match_shots["is_goal"] == True)]

    if not pal_goals.empty:
        pal_g_y = []
        pal_g_hover = []
        for _, pg in pal_goals.iterrows():
            y_pts = df_timeline[df_timeline["minute"] == pg["minute"]]["cum_palmeiras"].values
            pal_g_y.append(y_pts[0] if len(y_pts) > 0 else cum_pal)
            pal_g_hover.append(
                f"⚽ <b>GOL PALMEIRAS!</b><br>"
                f"{pg['player_name']} ({pg['minute']}')<br>"
                f"xG: {pg['xg']:.3f} | Dist: {pg['distance_meters']:.1f}m<br>"
                f"Situação: {pg['situation']}"
            )
        fig_timeline.add_trace(go.Scatter(
            x=pal_goals["minute"],
            y=pal_g_y,
            mode="markers",
            name="⚽ Gols Palmeiras",
            marker=dict(size=14, color="#00FF87", symbol="star", line=dict(color="white", width=1.5)),
            text=pal_g_hover,
            hoverinfo="text"
        ))

    if not opp_goals.empty:
        opp_g_y = []
        opp_g_hover = []
        for _, og in opp_goals.iterrows():
            y_pts = df_timeline[df_timeline["minute"] == og["minute"]]["cum_opponent"].values
            opp_g_y.append(y_pts[0] if len(y_pts) > 0 else cum_opp)
            opp_g_hover.append(
                f"⚽ <b>GOL {match_row['opponent_name'].upper()}!</b><br>"
                f"{og['player_name']} ({og['minute']}')<br>"
                f"xG: {og['xg']:.3f} | Dist: {og['distance_meters']:.1f}m<br>"
                f"Situação: {og['situation']}"
            )
        fig_timeline.add_trace(go.Scatter(
            x=opp_goals["minute"],
            y=opp_g_y,
            mode="markers",
            name=f"⚽ Gols {match_row['opponent_name']}",
            marker=dict(size=14, color="#FFD700", symbol="star", line=dict(color="white", width=1.5)),
            text=opp_g_hover,
            hoverinfo="text"
        ))

    fig_timeline.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="Minuto de Jogo",
        yaxis_title="xG Acumulado",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

    # Tabela Cronológica de Gols e Grandes Momentos da Partida
    key_events = match_shots[
        (match_shots["is_goal"] == True) | (match_shots["xg"] >= 0.20)
    ].sort_values(by=["minute", "time_seconds"])

    if not key_events.empty:
        st.markdown("##### 📜 Momentos Decisivos da Partida (Gols e Grandes Chances xG >= 0.20)")
        event_rows = []
        for _, r in key_events.iterrows():
            is_g = r["is_goal"]
            badge = "⚽ GOL" if is_g else ("🧤 Defesa" if r["outcome"] == "Defesa" else f"⚠️ {r['outcome']}")
            team = "Palmeiras" if r["is_palmeiras"] else match_row["opponent_name"]
            event_rows.append({
                "Minuto": f"{r['minute']}'" + (f" (+{r['added_time']})" if r['added_time'] > 0 else ""),
                "Equipe": team,
                "Evento": badge,
                "Jogador": r["player_name"],
                "xG": f"{r['xg']:.3f}",
                "Distância": f"{r['distance_meters']:.1f} m",
                "Situação": r["situation"],
                "Placar Antes": f"{r['score_palmeiras_before']} x {r['score_opponent_before']}"
            })
        st.dataframe(pd.DataFrame(event_rows), use_container_width=True, hide_index=True)

    # 3. Curva de Attack Momentum (Pressão de Ataque)
    st.markdown("#### 🌪️ Curva de Attack Momentum (Pressão Ofensiva Minuto a Minuto)")
    from src.ingestion.sofascore_client import SofaScoreClient
    from src.visualization.momentum_chart import plot_attack_momentum
    client = SofaScoreClient()
    graph_data = client.get_event_graph(selected_match_id, season_year=str(match_row["season"]))
    
    if graph_data and "graphPoints" in graph_data:
        fig_momentum = plot_attack_momentum(
            graph_data["graphPoints"],
            match_shots,
            is_palmeiras_home=bool(match_row["is_palmeiras_home"]),
            palmeiras_name="Palmeiras",
            opponent_name=str(match_row["opponent_name"])
        )
        st.plotly_chart(fig_momentum, use_container_width=True)
    else:
        st.info("Curva de momentum não disponível para este confronto específico.")

    # 4. Painel de Controle Territorial & Estatísticas Estruturais
    if "has_advanced_stats" in match_row and match_row["has_advanced_stats"]:
        st.markdown("#### 🏟️ Domínio Territorial & Ocupação do Terço Final")
        c_t1, c_t2, c_t3, c_t4 = st.columns(4)
        c_t1.metric("Field Tilt (Posse no Ataque)", f"{match_row.get('field_tilt', 50):.1f}%")
        c_t2.metric("Toques na Área Adversária", f"{match_row.get('palmeiras_touches_in_box', 0):.0f}", f"vs {match_row.get('opponent_touches_in_box', 0):.0f} do adv")
        c_t3.metric("Entradas no Terço Final", f"{match_row.get('palmeiras_final_third_entries', 0):.0f}", f"vs {match_row.get('opponent_final_third_entries', 0):.0f} do adv")
        c_t4.metric("Gols Evitados (Goleiro)", f"{match_row.get('palmeiras_goals_prevented', 0):+.2f}")

        c_f1, c_f2 = st.columns(2)
        c_f1.caption(f"**Formação Palmeiras:** {match_row.get('palmeiras_formation', '4-2-3-1')} | **Posse:** {match_row.get('palmeiras_possession', 50):.0f}% | **Cruzamentos:** {match_row.get('palmeiras_crosses_attempted', 0):.0f} ({match_row.get('palmeiras_crosses_acc_pct', 0):.0f}% acerto)")
        c_f2.caption(f"**Formação {match_row['opponent_name']}:** {match_row.get('opponent_formation', 'Não informada')} | **Posse:** {match_row.get('opponent_possession', 50):.0f}% | **Passes em Profundidade:** {match_row.get('palmeiras_through_balls', 0):.0f}")

    # Shotmap específico do jogo
    st.markdown("#### 🗺️ Finalizações da Partida")
    fig_match_pitch = plot_interactive_shotmap(match_shots, title=f"Shotmap do Confronto: {match_row['home_team']} x {match_row['away_team']}")
    st.plotly_chart(fig_match_pitch, use_container_width=True)

    # 5. Guia Metodológico
    with st.expander("📖 Guia Tático: O que esta tela responde e como interpretar"):
        st.markdown(r"""
        **1. Qual pergunta queremos responder?**
        - O placar final da partida refletiu com justiça as chances criadas por cada equipe ou o resultado foi determinado pela aleatoriedade do futebol?
        - A equipe teve domínio territorial real ou teve posse inócua no próprio campo?
        
        **2. Dicionário de Variáveis e Dados:**
        - **Simulação Monte Carlo (10.000 iterações):** Cada finalização de Palmeiras e adversário é simulada como um sorteio binomial ponderado pelo seu valor de xG exato. Contabilizamos o percentual de jogos em que o Palmeiras sairia vitorioso, empataria ou seria derrotado.
        - **Pontos Esperados (xPTS):** $3 \times P(\text{Vitória}) + 1 \times P(\text{Empate})$.
        - **Attack Momentum:** Índice gerado pela API do SofaScore que monitora a pressão ofensiva a cada minuto (-100 a +100), combinando posse ofensiva, desarmes no ataque e escanteios.
        - **Field Tilt (%):** Proporção das entradas no terço final que pertenceram ao Palmeiras. Ex: se o Palmeiras entrou 60 vezes e o rival 40, o Field Tilt é $60\%$.
        
        **3. O Mito Desmontado:**
        - Uma equipe pode vencer de 1x0 com um gol de falta de 0.03 xG e ter $P(\text{Vitória}) = 15\%$. A simulação protege analistas de superestimar atuações fracas que terminaram em vitória por acaso.
        """)
