# -*- coding: utf-8 -*-
"""
View 2: O que Mudou? (Comparador Tático & Diagnóstico Causal).
O coração analítico do projeto:
- Seletor Unificado Global (Temporadas ou Turnos do Brasileirão)
- Quadro Executivo Imediato: Pontos Positivos vs. Pontos Negativos
- A Anatomia Causal dos Resultados: Ataque vs Defesa, Big Chances e Goleiros
- Protagonistas da Mudança: Divergência de Conversão e Tabela de Deltas Colorida
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def render_comparison_view(df_shots_full: pd.DataFrame, df_matches_full: pd.DataFrame):
    st.markdown("### ⚔️ O que Mudou? (Comparador Tático & Diagnóstico Causal)")
    st.caption("Responde por que o rendimento subiu ou caiu tanto: pontos positivos, pontos negativos, causas defensivas e protagonistas.")

    if df_matches_full.empty or df_shots_full.empty:
        st.warning("Dados não disponíveis para comparação.")
        return

    pal_shots_all = df_shots_full[df_shots_full["is_palmeiras"] == True].copy()
    all_seasons = sorted(list(df_matches_full["season"].dropna().unique()), reverse=True)
    bra_m = df_matches_full[df_matches_full["tournament"].str.contains("Brasileir", case=False)].copy()

    # -------------------------------------------------------------------------
    # 1. SELETOR UNIFICADO NO TOPO
    # -------------------------------------------------------------------------
    c_mode, c_sel = st.columns([1.1, 2.9])
    with c_mode:
        comp_mode = st.radio(
            "Recorte de Comparação:",
            ["🔄 Entre Turnos do Brasileirão", "📅 Entre Temporadas Completas", "🏆 Entre Competições"],
            index=0,
            key="v2_comp_mode"
        )

    with c_sel:
        if comp_mode == "📅 Entre Temporadas Completas":
            c1, c2, c3 = st.columns(3)
            with c1:
                def_b = min(1, len(all_seasons) - 1)
                base_season = st.selectbox("Temporada Base (Referência):", all_seasons, index=def_b, key="v2_base_s")
            with c2:
                target_season = st.selectbox("Temporada Alvo (Comparação):", all_seasons, index=0, key="v2_target_s")
            with c3:
                tourn_opts = ["Todas as Competições"] + sorted(list(df_matches_full["tournament"].dropna().unique()))
                comp_filter = st.selectbox("Competição:", tourn_opts, key="v2_tourn_filter")

            m_base = df_matches_full[df_matches_full["season"] == base_season]
            m_target = df_matches_full[df_matches_full["season"] == target_season]
            if comp_filter != "Todas as Competições":
                m_base = m_base[m_base["tournament"] == comp_filter]
                m_target = m_target[m_target["tournament"] == comp_filter]

            label_base = f"{base_season}" + (f" ({comp_filter})" if comp_filter != "Todas as Competições" else "")
            label_target = f"{target_season}" + (f" ({comp_filter})" if comp_filter != "Todas as Competições" else "")

        elif comp_mode == "🔄 Entre Turnos do Brasileirão":
            turno_options = []
            for s_yr in sorted(list(bra_m["season"].dropna().unique()), reverse=True):
                sub = bra_m[bra_m["season"] == s_yr]
                for t in ["2º Turno", "1º Turno"]:
                    if t in sub["turno"].unique():
                        turno_options.append(f"{s_yr} - {t}")

            c1, c2 = st.columns(2)
            with c1:
                def_b_idx = turno_options.index("2026 - 1º Turno") if "2026 - 1º Turno" in turno_options else min(1, len(turno_options)-1)
                base_turno = st.selectbox("Turno Base (Referência):", turno_options, index=def_b_idx, key="v2_base_t")
            with c2:
                def_t_idx = turno_options.index("2026 - 2º Turno") if "2026 - 2º Turno" in turno_options else 0
                target_turno = st.selectbox("Turno Alvo (Comparação):", turno_options, index=def_t_idx, key="v2_target_t")

            b_yr, b_t = base_turno.split(" - ")
            t_yr, t_t = target_turno.split(" - ")

            m_base = bra_m[(bra_m["season"] == b_yr) & (bra_m["turno"] == b_t)]
            m_target = bra_m[(bra_m["season"] == t_yr) & (bra_m["turno"] == t_t)]
            label_base = base_turno
            label_target = target_turno

        else: # Entre Competições
            all_tourns = sorted(list(df_matches_full["tournament"].dropna().unique()))
            c1, c2, c3 = st.columns(3)
            with c1:
                base_tourn = st.selectbox("Competição Base (Referência):", all_tourns, index=0, key="v2_base_tr")
            with c2:
                target_tourn = st.selectbox("Competição Alvo (Comparação):", all_tourns, index=min(1, len(all_tourns)-1), key="v2_target_tr")
            with c3:
                s_opt = st.selectbox("Temporada:", ["Todas as Temporadas"] + all_seasons, key="v2_tr_s")

            m_base = df_matches_full[df_matches_full["tournament"] == base_tourn]
            m_target = df_matches_full[df_matches_full["tournament"] == target_tourn]
            if s_opt != "Todas as Temporadas":
                m_base = m_base[m_base["season"] == s_opt]
                m_target = m_target[m_target["season"] == s_opt]

            label_base = f"{base_tourn}" + (f" ({s_opt})" if s_opt != "Todas as Temporadas" else "")
            label_target = f"{target_tourn}" + (f" ({s_opt})" if s_opt != "Todas as Temporadas" else "")

    s_base = pal_shots_all[pal_shots_all["match_id"].isin(m_base["match_id"])].copy()
    s_target = pal_shots_all[pal_shots_all["match_id"].isin(m_target["match_id"])].copy()

    n_m_base = len(m_base)
    n_m_target = len(m_target)
    n_s_base = len(s_base)
    n_s_target = len(s_target)

    # Banner de Contexto Ativo
    st.markdown(
        f"""
        <div style="background-color: #1A2332; padding: 12px 18px; border-radius: 8px; border-left: 5px solid #00FF87; margin-bottom: 20px;">
            <span style="font-size: 1.05rem; font-weight: bold; color: #FFFFFF;">📊 Comparação Ativa:</span>
            &nbsp;&nbsp;
            <span style="color: #00BFFF; font-weight: 600;">🔵 Base: {label_base}</span> ({n_m_base} jogos, {n_s_base} chutes)
            &nbsp;&nbsp;<b>VS</b>&nbsp;&nbsp;
            <span style="color: #00FF87; font-weight: 600;">🟢 Alvo: {label_target}</span> ({n_m_target} jogos, {n_s_target} chutes)
        </div>
        """,
        unsafe_allow_html=True
    )

    if n_m_base == 0 or n_m_target == 0 or n_s_base == 0 or n_s_target == 0:
        st.warning(f"Dados insuficientes para comparar '{label_base}' ({n_m_base} jogos) com '{label_target}' ({n_m_target} jogos). Selecione outros recortes acima.")
        return

    # Cálculos Matemáticos e Fatoriais
    v_base = n_s_base / n_m_base
    v_target = n_s_target / n_m_target
    xg_total_b = s_base["xg"].sum()
    xg_total_t = s_target["xg"].sum()
    xg90_base = xg_total_b / n_m_base
    xg90_target = xg_total_t / n_m_target

    gols_pro_b = m_base["palmeiras_goals"].sum()
    gols_pro_t = m_target["palmeiras_goals"].sum()
    gp90_b = gols_pro_b / n_m_base
    gp90_t = gols_pro_t / n_m_target

    gols_contra_b = m_base["opponent_goals"].sum()
    gols_contra_t = m_target["opponent_goals"].sum()
    gc90_b = gols_contra_b / n_m_base
    gc90_t = gols_contra_t / n_m_target

    xg_contra_b = m_base["opponent_xg"].sum()
    xg_contra_t = m_target["opponent_xg"].sum()
    xgc90_b = xg_contra_b / n_m_base
    xgc90_t = xg_contra_t / n_m_target

    vits_b = (m_base["result"] == "Vitória").sum()
    vits_t = (m_target["result"] == "Vitória").sum()
    aprov_b = ((vits_b * 3 + (m_base["result"] == "Empate").sum()) / (n_m_base * 3) * 100)
    aprov_t = ((vits_t * 3 + (m_target["result"] == "Empate").sum()) / (n_m_target * 3) * 100)

    delta_xg = xg90_target - xg90_base
    delta_v = v_target - v_base
    delta_gp = gp90_t - gp90_b
    delta_gc = gc90_t - gc90_b
    delta_xgc = xgc90_t - xgc90_b
    delta_aprov = aprov_t - aprov_b

    # Big Chances e Goals Prevented
    bc_pro_b = m_base["big_chances_palmeiras"].mean() if "big_chances_palmeiras" in m_base.columns else 0
    bc_pro_t = m_target["big_chances_palmeiras"].mean() if "big_chances_palmeiras" in m_target.columns else 0
    bc_opp_b = m_base["big_chances_opponent"].mean() if "big_chances_opponent" in m_base.columns else 0
    bc_opp_t = m_target["big_chances_opponent"].mean() if "big_chances_opponent" in m_target.columns else 0

    gp_pal_b = m_base["palmeiras_goals_prevented"].mean() if "palmeiras_goals_prevented" in m_base.columns else 0
    gp_pal_t = m_target["palmeiras_goals_prevented"].mean() if "palmeiras_goals_prevented" in m_target.columns else 0
    gp_opp_b = m_base["opponent_goals_prevented"].mean() if "opponent_goals_prevented" in m_base.columns else 0
    gp_opp_t = m_target["opponent_goals_prevented"].mean() if "opponent_goals_prevented" in m_target.columns else 0

    eff_conv_b = (gols_pro_b / xg_total_b - 1.0) * 100 if xg_total_b > 0 else 0
    eff_conv_t = (gols_pro_t / xg_total_t - 1.0) * 100 if xg_total_t > 0 else 0

    # -------------------------------------------------------------------------
    # 2. QUADRO EXECUTIVO: PONTOS POSITIVOS VS PONTOS NEGATIVOS
    # -------------------------------------------------------------------------
    st.markdown("#### 📋 Quadro Executivo: O que Melhorou vs. O que Piorou?")
    st.caption("Visão gráfica das oscilações estatísticas reais entre os dois períodos (Tornado Chart de Impacto Relativo).")

    # Construção dos indicadores do Tornado Chart
    tornado_items = []

    # 1. Criação Ofensiva
    if xg90_base > 0:
        pct_xg = ((xg90_target - xg90_base) / xg90_base) * 100
        tornado_items.append({
            "Indicador": "Criação de Perigo (xG/90)",
            "Impacto": pct_xg,
            "Rotulo": f"{pct_xg:+.1f}% ({delta_xg:+.2f} xG/j)",
            "Detalhe": f"Base: {xg90_base:.2f} ➔ Alvo: {xg90_target:.2f} xG/j",
            "Sentido": "Positivo" if pct_xg >= 0 else "Negativo"
        })

    # 2. Grandes Chances Criadas
    if bc_pro_b > 0:
        pct_bc_pro = ((bc_pro_t - bc_pro_b) / bc_pro_b) * 100
        tornado_items.append({
            "Indicador": "Grandes Chances Criadas/j",
            "Impacto": pct_bc_pro,
            "Rotulo": f"{pct_bc_pro:+.1f}% ({bc_pro_t - bc_pro_b:+.2f}/j)",
            "Detalhe": f"Base: {bc_pro_b:.2f} ➔ Alvo: {bc_pro_t:.2f} por jogo",
            "Sentido": "Positivo" if pct_bc_pro >= 0 else "Negativo"
        })

    # 3. Volume de Finalizações
    if v_base > 0:
        pct_v = ((v_target - v_base) / v_base) * 100
        tornado_items.append({
            "Indicador": "Volume de Chutes/j",
            "Impacto": pct_v,
            "Rotulo": f"{pct_v:+.1f}% ({delta_v:+.1f} chutes)",
            "Detalhe": f"Base: {v_base:.1f} ➔ Alvo: {v_target:.1f} chutes/j",
            "Sentido": "Positivo" if pct_v >= 0 else "Negativo"
        })

    # 4. Solidez Defensiva (xG Sofrido) -> Invertido: sofrer mais xG é impacto negativo para o time
    if xgc90_b > 0:
        pct_xgc_impact = -((xgc90_t - xgc90_b) / xgc90_b) * 100
        tornado_items.append({
            "Indicador": "Solidez Defensiva (xG Sofrido)",
            "Impacto": pct_xgc_impact,
            "Rotulo": f"{pct_xgc_impact:+.1f}% ({delta_xgc:+.2f} xGC/j)",
            "Detalhe": f"Base: {xgc90_b:.2f} ➔ Alvo: {xgc90_t:.2f} xG sofrido/j",
            "Sentido": "Positivo" if pct_xgc_impact >= 0 else "Negativo"
        })

    # 5. Grandes Chances Cedidas -> Invertido
    if bc_opp_b > 0:
        pct_bc_opp_impact = -((bc_opp_t - bc_opp_b) / bc_opp_b) * 100
        tornado_items.append({
            "Indicador": "Controle de Big Chances Cedidas",
            "Impacto": pct_bc_opp_impact,
            "Rotulo": f"{pct_bc_opp_impact:+.1f}% ({bc_opp_t - bc_opp_b:+.2f}/j)",
            "Detalhe": f"Base: {bc_opp_b:.2f} ➔ Alvo: {bc_opp_t:.2f} cedidas/j",
            "Sentido": "Positivo" if pct_bc_opp_impact >= 0 else "Negativo"
        })

    # 6. Conversão / Letalidade vs. xG
    delta_eff_conv = eff_conv_t - eff_conv_b
    tornado_items.append({
        "Indicador": "Letalidade / Conversão vs. xG",
        "Impacto": delta_eff_conv,
        "Rotulo": f"{delta_eff_conv:+.1f}% ({eff_conv_b:+.1f}% ➔ {eff_conv_t:+.1f}%)",
        "Detalhe": f"Conversão de gols acima/abaixo do xG",
        "Sentido": "Positivo" if delta_eff_conv >= 0 else "Negativo"
    })

    # 7. Aproveitamento de Pontos
    tornado_items.append({
        "Indicador": "Aproveitamento de Pontos (%)",
        "Impacto": delta_aprov,
        "Rotulo": f"{delta_aprov:+.1f}% ({aprov_b:.1f}% ➔ {aprov_t:.1f}%)",
        "Detalhe": f"Pontos conquistados vs disputados",
        "Sentido": "Positivo" if delta_aprov >= 0 else "Negativo"
    })

    df_tornado = pd.DataFrame(tornado_items).sort_values(by="Impacto", ascending=True)

    fig_tornado = go.Figure()
    for _, row in df_tornado.iterrows():
        color = "#00FF87" if row["Sentido"] == "Positivo" else "#FF4B4B"
        fig_tornado.add_trace(go.Bar(
            y=[row["Indicador"]],
            x=[row["Impacto"]],
            orientation="h",
            marker=dict(color=color),
            text=[f"  {row['Rotulo']}  "],
            textposition="outside",
            hoverinfo="text",
            hovertext=[f"<b>{row['Indicador']}</b><br>{row['Detalhe']}<br>Impacto: {row['Rotulo']}"],
            showlegend=False
        ))

    max_abs = max(df_tornado["Impacto"].abs().max() * 1.35, 35)
    fig_tornado.add_vline(x=0, line_color="#888888", line_width=1.5)
    fig_tornado.update_layout(
        template="plotly_dark",
        height=320,
        margin=dict(l=10, r=25, t=10, b=10),
        xaxis=dict(
            title="Impacto no Rendimento do Palmeiras (◀ Regressão | Avanço ▶)",
            range=[-max_abs, max_abs],
            zeroline=False
        ),
        yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig_tornado, use_container_width=True)

    # Síntese Executiva Rápida em Cards Complementares
    import re
    def to_html_bold(s: str) -> str:
        return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', str(s))

    positives = []
    negatives = []

    if delta_xg > 0.05:
        positives.append(f"<b>Criação Ofensiva:</b> xG/90 subiu em <b>{delta_xg:+.2f}</b> ({xg90_base:.2f} ➔ {xg90_target:.2f} xG/j).")
    elif delta_xg < -0.05:
        negatives.append(f"<b>Criação Ofensiva:</b> xG/90 caiu em <b>{delta_xg:+.2f}</b> ({xg90_base:.2f} ➔ {xg90_target:.2f} xG/j).")

    if bc_pro_t > bc_pro_b + 0.2:
        positives.append(f"<b>Grandes Chances:</b> Produção claríssima subiu para <b>{bc_pro_t:.2f}/j</b> (+{bc_pro_t - bc_pro_b:.2f} vs Base).")

    if delta_xgc > 0.15:
        negatives.append(f"<b>Exposição Defensiva:</b> xG sofrido subiu em <b>{delta_xgc:+.2f} xGC/j</b> ({xgc90_b:.2f} ➔ {xgc90_t:.2f}).")
    elif delta_xgc < -0.15:
        positives.append(f"<b>Solidez Defensiva:</b> xG sofrido caiu em <b>{abs(delta_xgc):.2f} xGC/j</b> ({xgc90_b:.2f} ➔ {xgc90_t:.2f}).")

    if eff_conv_b > 25 and eff_conv_t < eff_conv_b - 15:
        negatives.append(f"<b>Letalidade:</b> Conversão anormal da base (+{eff_conv_b:.1f}%) normalizou no alvo ({eff_conv_t:+.1f}% vs xG).")
    elif eff_conv_t > eff_conv_b + 15:
        positives.append(f"<b>Letalidade Clínica:</b> Ataque converteu <b>{eff_conv_t:+.1f}%</b> acima da expectativa xG.")

    if not positives:
        positives.append("Parâmetros de volume e criação mantiveram-se estáveis.")
    if not negatives:
        negatives.append("Nenhum indicador crítico registrou declínio acentuado.")

    c_box1, c_box2 = st.columns(2)
    with c_box1:
        st.markdown(
            f"""
            <div style="background-color: #122416; border: 1.5px solid #00FF87; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
                <h5 style="color: #00FF87; margin-top: 0; margin-bottom: 8px;">✅ Principais Ganhos (Destaques Positivos)</h5>
                <ul style="color: #E2E8F0; font-size: 0.88rem; line-height: 1.5; margin-bottom: 0; padding-left: 18px;">
                    {''.join([f'<li>{to_html_bold(p)}</li>' for p in positives])}
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c_box2:
        st.markdown(
            f"""
            <div style="background-color: #261618; border: 1.5px solid #FF4B4B; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
                <h5 style="color: #FF4B4B; margin-top: 0; margin-bottom: 8px;">❌ Principais Perdas (Destaques Negativos)</h5>
                <ul style="color: #E2E8F0; font-size: 0.88rem; line-height: 1.5; margin-bottom: 0; padding-left: 18px;">
                    {''.join([f'<li>{to_html_bold(n)}</li>' for n in negatives])}
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. ANATOMIA CAUSAL DO RESULTADO (POR QUE O RENDIMENTO MUDOU?)
    # -------------------------------------------------------------------------
    st.markdown("#### ⚖️ Anatomia Causal do Resultado: O Balanço Ataque vs. Defesa")
    st.caption("Entenda por que vitórias foram conquistadas ou perdidas analisando conjuntamente o ataque e a defesa.")

    col_atk, col_def = st.columns(2)

    with col_atk:
        st.markdown("##### ⚔️ Produção Ofensiva (Criação xG vs. Gols Marcados)")
        st.caption("Compara o perigo que o Palmeiras criou com as bolas que efetivamente entraram na rede.")

        gp90_b_round = round(gp90_b + 1e-9, 2)
        gp90_t_round = round(gp90_t + 1e-9, 2)
        xg90_b_round = round(xg90_base, 2)
        xg90_t_round = round(xg90_target, 2)

        fig_of = go.Figure()
        fig_of.add_trace(go.Bar(
            x=[label_base, label_target], y=[xg90_b_round, xg90_t_round],
            name="xG Pró / 90 min (Criação)", marker_color="#00BFFF",
            text=[f"{xg90_b_round:.2f} ({xg_total_b:.1f} xG)", f"{xg90_t_round:.2f} ({xg_total_t:.1f} xG)"],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Criação: <b>%{y:.2f} xG/jogo</b><br>Total acumulado: " + f"{xg_total_b:.2f} xG em {n_m_base} jogos" + "<extra></extra>"
        ))
        fig_of.add_trace(go.Bar(
            x=[label_base, label_target], y=[gp90_b_round, gp90_t_round],
            name="Gols Pró / 90 min (Rede)", marker_color="#00FF87",
            text=[f"{gp90_b_round:.2f} ({int(gols_pro_b)}G)", f"{gp90_t_round:.2f} ({int(gols_pro_t)}G)"],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Gols Reais: <b>%{y:.2f} gols/jogo</b><br>Total acumulado: " + f"{int(gols_pro_b)} gols em {n_m_base} jogos" + "<extra></extra>"
        ))
        fig_of.update_layout(
            template="plotly_dark", height=320, barmode="group",
            margin=dict(l=10, r=10, t=25, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_of, use_container_width=True)

    with col_def:
        st.markdown("##### 🛡️ Solidez Defensiva (Perigo Sofrido xG vs. Gols Tomados)")
        st.caption("Compara o perigo concedido aos rivais com os gols que o Palmeiras efetivamente sofreu.")

        gc90_b_round = round(gc90_b + 1e-9, 2)
        gc90_t_round = round(gc90_t + 1e-9, 2)
        xgc90_b_round = round(xgc90_b, 2)
        xgc90_t_round = round(xgc90_t, 2)

        fig_def = go.Figure()
        fig_def.add_trace(go.Bar(
            x=[label_base, label_target], y=[xgc90_b_round, xgc90_t_round],
            name="xG Sofrido / 90 min (Perigo)", marker_color="#00BFFF",
            text=[f"{xgc90_b_round:.2f} ({xg_contra_b:.1f} xG)", f"{xgc90_t_round:.2f} ({xg_contra_t:.1f} xG)"],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Perigo Cedido: <b>%{y:.2f} xG sofrido/j</b><br>Total cedido: " + f"{xg_contra_b:.2f} xG em {n_m_base} jogos" + "<extra></extra>"
        ))
        fig_def.add_trace(go.Bar(
            x=[label_base, label_target], y=[gc90_b_round, gc90_t_round],
            name="Gols Sofridos / 90 min (Rede)", marker_color="#FF4B4B",
            text=[f"{gc90_b_round:.2f} ({int(gols_contra_b)}G)", f"{gc90_t_round:.2f} ({int(gols_contra_t)}G)"],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Gols Sofridos: <b>%{y:.2f} sofridos/j</b><br>Total sofrido: " + f"{int(gols_contra_b)} gols em {n_m_base} jogos" + "<extra></extra>"
        ))
        fig_def.update_layout(
            template="plotly_dark", height=320, barmode="group",
            margin=dict(l=10, r=10, t=25, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_def, use_container_width=True)

    # Informações Relevantes Adicionais (Big Chances, Goleiros e Saldo)
    st.markdown("##### 🎯 Eficiência & Fatores Decisivos (Chances Claras, Goleiros e Justiça do Placar)")
    st.caption("Descubra se o placar final refletiu o volume de jogo: o time criou chances fáceis? Os goleiros fizeram milagres ou falharam?")

    c_f1, c_f2, c_f3 = st.columns(3)

    with c_f1:
        st.markdown("###### ⭐ Grandes Chances / Jogo (Cara a Cara)")
        st.caption("Chances claríssimas de gol (frente a frente com a trave ou pequena área).")
        fig_bc = go.Figure()
        fig_bc.add_trace(go.Bar(
            x=[label_base, label_target], y=[round(bc_pro_b, 2), round(bc_pro_t, 2)],
            name="Grandes Chances Criadas", marker_color="#00FF87",
            text=[f"{bc_pro_b:.2f}", f"{bc_pro_t:.2f}"], textposition="outside"
        ))
        fig_bc.add_trace(go.Bar(
            x=[label_base, label_target], y=[round(bc_opp_b, 2), round(bc_opp_t, 2)],
            name="Grandes Chances Cedidas", marker_color="#FF4B4B",
            text=[f"{bc_opp_b:.2f}", f"{bc_opp_t:.2f}"], textposition="outside"
        ))
        fig_bc.update_layout(
            template="plotly_dark", height=280, barmode="group",
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_bc, use_container_width=True)

    with c_f2:
        st.markdown("###### 🧤 Gols Evitados pelos Goleiros por Jogo")
        st.caption("Gols certos que os goleiros defenderam além da expectativa por partida. Positivo = operou milagres; Negativo = levou frangos.")
        fig_gp = go.Figure()
        fig_gp.add_trace(go.Bar(
            x=[label_base, label_target], y=[round(gp_pal_b, 2), round(gp_pal_t, 2)],
            name="Goleiros do Palmeiras", marker_color="#00BFFF",
            text=[f"{gp_pal_b:+.2f}/j", f"{gp_pal_t:+.2f}/j"], textposition="outside",
            hovertemplate="<b>Palmeiras</b>: %{y:+.2f} gols evitados por partida<extra></extra>"
        ))
        fig_gp.add_trace(go.Bar(
            x=[label_base, label_target], y=[round(gp_opp_b, 2), round(gp_opp_t, 2)],
            name="Goleiros Adversários", marker_color="#FFA500",
            text=[f"{gp_opp_b:+.2f}/j", f"{gp_opp_t:+.2f}/j"], textposition="outside",
            hovertemplate="<b>Adversários</b>: %{y:+.2f} gols evitados por partida<extra></extra>"
        ))
        fig_gp.update_layout(
            template="plotly_dark", height=280, barmode="group",
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_gp, use_container_width=True)
        st.caption("📖 <b>O que é essa métrica:</b> Compara a dificuldade dos chutes no alvo contra os gols sofridos. Ex: +0.61/j significa que o goleiro salvou 0.61 gol certo por jogo.")

    with c_f3:
        st.markdown("###### ⚖️ Saldo de Gols / Jogo (Placar Real vs. Chances)")
        st.caption("Compara a margem de gols no placar (Gols Feitos − Tomados) contra a margem justa pelas chances (xG Criado − Cedido).")
        saldo_real_b = gp90_b - gc90_b
        saldo_real_t = gp90_t - gc90_t
        saldo_xg_b = xg90_base - xgc90_b
        saldo_xg_t = xg90_target - xgc90_t

        fig_s = go.Figure()
        fig_s.add_trace(go.Bar(
            x=[label_base, label_target], y=[round(saldo_real_b, 2), round(saldo_real_t, 2)],
            name="Saldo Real (Placar: Feitos − Tomados)", marker_color="#00FF87",
            text=[f"{saldo_real_b:+.2f}", f"{saldo_real_t:+.2f}"], textposition="outside",
            hovertemplate="<b>Saldo Real</b>: %{y:+.2f} gols por jogo<extra></extra>"
        ))
        fig_s.add_trace(go.Bar(
            x=[label_base, label_target], y=[round(saldo_xg_b, 2), round(saldo_xg_t, 2)],
            name="Saldo Esperado (Chances: xG Criado − Cedido)", marker_color="#00BFFF",
            text=[f"{saldo_xg_b:+.2f}", f"{saldo_xg_t:+.2f}"], textposition="outside",
            hovertemplate="<b>Saldo Esperado (xG)</b>: %{y:+.2f} xG por jogo<extra></extra>"
        ))
        fig_s.update_layout(
            template="plotly_dark", height=280, barmode="group",
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_s, use_container_width=True)
        st.caption("📖 <b>O que é 'Saldo':</b> É a margem média por partida (Ataque − Defesa). Se a barra verde for maior que a azul, o time teve placares mais folgados do que o perigo justificava.")

    # =========================================================================
    # NOVA SEÇÃO A — GAME STATE POR PERÍODO
    # =========================================================================
    st.markdown("---")
    st.markdown("#### ⏱️ Análise de Game State: Como o Palmeiras Joga em Cada Placar?")
    st.caption(
        "Decompõe o xG por estado de jogo (Vencendo / Empatando / Perdendo) para responder a pergunta crucial: "
        "o volume de criação mudou estruturalmente, ou simplesmente o time passou mais tempo em determinados estados de placar?"
    )

    # Aggregate minutes per game state
    _gs_cols = {"minutes_winning": "Vencendo", "minutes_drawing": "Empatando", "minutes_losing": "Perdendo"}
    _gs_data = []
    for col, label in _gs_cols.items():
        if col in m_base.columns and col in m_target.columns:
            min_b = m_base[col].sum()
            min_t = m_target[col].sum()
            # xG by game state from shots
            gs_key = label
            xg_gs_b = s_base[s_base["game_state"] == gs_key]["xg"].sum() if "game_state" in s_base.columns else 0
            xg_gs_t = s_target[s_target["game_state"] == gs_key]["xg"].sum() if "game_state" in s_target.columns else 0
            xg90_gs_b = (xg_gs_b / max(1, min_b)) * 90 if min_b > 0 else 0
            xg90_gs_t = (xg_gs_t / max(1, min_t)) * 90 if min_t > 0 else 0
            pct_min_b = (min_b / max(1, m_base[list(_gs_cols.keys())].sum(axis=1).sum() / n_m_base / 90 * n_m_base * 90)) * 100 if min_b > 0 else 0
            pct_min_t = (min_t / max(1, m_target[list(_gs_cols.keys())].sum(axis=1).sum() / n_m_target / 90 * n_m_target * 90)) * 100 if min_t > 0 else 0
            _gs_data.append({
                "Estado": gs_key, "Min Base": int(min_b), "Min Alvo": int(min_t),
                "xG/90 Base": round(xg90_gs_b, 2), "xG/90 Alvo": round(xg90_gs_t, 2),
                "Δ xG/90": round(xg90_gs_t - xg90_gs_b, 2)
            })

    if _gs_data:
        _gs_df = pd.DataFrame(_gs_data)
        _c_gs1, _c_gs2 = st.columns([1.1, 1.0])
        with _c_gs1:
            st.markdown("##### 📊 Minutos por Estado de Jogo (Base vs Alvo)")
            _fig_gs_min = go.Figure()
            _fig_gs_min.add_trace(go.Bar(
                name=f"Base: {label_base}", x=_gs_df["Estado"], y=_gs_df["Min Base"],
                marker_color="#00BFFF", text=_gs_df["Min Base"].apply(lambda v: f"{v}min"),
                textposition="outside"
            ))
            _fig_gs_min.add_trace(go.Bar(
                name=f"Alvo: {label_target}", x=_gs_df["Estado"], y=_gs_df["Min Alvo"],
                marker_color="#00FF87", text=_gs_df["Min Alvo"].apply(lambda v: f"{v}min"),
                textposition="outside"
            ))
            _fig_gs_min.update_layout(
                template="plotly_dark", height=300, barmode="group",
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(_fig_gs_min, use_container_width=True)

        with _c_gs2:
            st.markdown("##### 🎯 xG/90 Normalizado por Estado de Jogo")
            _fig_gs_xg = go.Figure()
            _fig_gs_xg.add_trace(go.Bar(
                name=f"Base: {label_base}", x=_gs_df["Estado"], y=_gs_df["xG/90 Base"],
                marker_color="#00BFFF", text=_gs_df["xG/90 Base"].apply(lambda v: f"{v:.2f}"),
                textposition="outside"
            ))
            _fig_gs_xg.add_trace(go.Bar(
                name=f"Alvo: {label_target}", x=_gs_df["Estado"], y=_gs_df["xG/90 Alvo"],
                marker_color="#00FF87", text=_gs_df["xG/90 Alvo"].apply(lambda v: f"{v:.2f}"),
                textposition="outside"
            ))
            _fig_gs_xg.update_layout(
                template="plotly_dark", height=300, barmode="group",
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                yaxis_title="xG/90 (normalizado por minutos)"
            )
            st.plotly_chart(_fig_gs_xg, use_container_width=True)

        # Insight automático de game state
        _gs_venc_b = _gs_df[_gs_df["Estado"] == "Vencendo"]["Min Base"].values[0] if len(_gs_df[_gs_df["Estado"] == "Vencendo"]) > 0 else 0
        _gs_venc_t = _gs_df[_gs_df["Estado"] == "Vencendo"]["Min Alvo"].values[0] if len(_gs_df[_gs_df["Estado"] == "Vencendo"]) > 0 else 0
        _gs_perd_b = _gs_df[_gs_df["Estado"] == "Perdendo"]["Min Base"].values[0] if len(_gs_df[_gs_df["Estado"] == "Perdendo"]) > 0 else 0
        _gs_perd_t = _gs_df[_gs_df["Estado"] == "Perdendo"]["Min Alvo"].values[0] if len(_gs_df[_gs_df["Estado"] == "Perdendo"]) > 0 else 0

        if _gs_venc_t > _gs_venc_b + 30:
            _gs_insight = f"⬆️ No período alvo (<b>{label_target}</b>), o time passou <b>mais minutos vencendo</b> (+{_gs_venc_t - _gs_venc_b}min) — sinal de superioridade crescente que naturalmente comprime o ataque adversário."
        elif _gs_perd_t > _gs_perd_b + 30:
            _gs_insight = f"⚠️ No período alvo (<b>{label_target}</b>), o time passou <b>mais minutos perdendo</b> (+{_gs_perd_t - _gs_perd_b}min) — equipes atrás no placar tendem a atacar mais, o que pode inflar artificialmente o volume ofensivo."
        else:
            _gs_insight = f"↔️ A distribuição de minutos por estado de jogo foi similar entre <b>{label_base}</b> e <b>{label_target}</b> — variações de xG refletem mudanças estruturais, não apenas diferença de contexto de placar."

        st.markdown(f"<div style='background:#0e1e28; border-left:3px solid #F59E0B; border-radius:4px; padding:10px 16px; font-size:0.86rem; color:#E2E8F0;'>💡 <b>Leitura do Game State:</b> {_gs_insight}</div>", unsafe_allow_html=True)

    # =========================================================================
    # NOVA SEÇÃO B — DECOMPOSIÇÃO POR SITUAÇÃO TÁTICA
    # =========================================================================
    st.markdown("---")
    st.markdown("#### 🎭 Anatomia da Criação: Como o xG é Construído em Cada Período?")
    st.caption(
        "Decompõe o xG por situação tática (Jogo Aberto, Bola Parada, Contra-Ataque, Pênalti) para entender "
        "se a mudança de rendimento veio de uma mudança no estilo de jogo ou apenas no volume."
    )

    if "situation" in s_base.columns and "situation" in s_target.columns:
        _sit_b = s_base.groupby("situation").agg(
            xg_b=("xg", "sum"), shots_b=("shot_id", "count"), goals_b=("is_goal", "sum")
        ).reset_index()
        _sit_t = s_target.groupby("situation").agg(
            xg_t=("xg", "sum"), shots_t=("shot_id", "count"), goals_t=("is_goal", "sum")
        ).reset_index()
        _sit = pd.merge(_sit_b, _sit_t, on="situation", how="outer").fillna(0)
        _sit["pct_xg_b"] = (_sit["xg_b"] / max(0.001, _sit["xg_b"].sum()) * 100).round(1)
        _sit["pct_xg_t"] = (_sit["xg_t"] / max(0.001, _sit["xg_t"].sum()) * 100).round(1)
        _sit["xg_per_shot_b"] = (_sit["xg_b"] / _sit["shots_b"].replace(0, np.nan)).round(3)
        _sit["xg_per_shot_t"] = (_sit["xg_t"] / _sit["shots_t"].replace(0, np.nan)).round(3)
        _sit["conv_b"] = (_sit["goals_b"] / _sit["xg_b"].replace(0, np.nan)).round(2)
        _sit["conv_t"] = (_sit["goals_t"] / _sit["xg_t"].replace(0, np.nan)).round(2)
        _sit = _sit.sort_values("xg_b", ascending=False)

        _c_sit1, _c_sit2 = st.columns(2)
        with _c_sit1:
            st.markdown("##### 📊 Share de xG por Situação Tática")
            _sit_colors = {"Jogo Aberto": "#00FF87", "Escanteio": "#00BFFF", "Falta / Bola Parada": "#F59E0B",
                           "Contra-Ataque": "#FF4B4B", "Pênalti": "#A855F7"}
            _fig_sit = go.Figure()
            _fig_sit.add_trace(go.Bar(
                name=f"Base: {label_base}", x=_sit["situation"], y=_sit["pct_xg_b"],
                marker_color=[_sit_colors.get(s, "#888") for s in _sit["situation"]],
                opacity=0.65,
                text=_sit["pct_xg_b"].apply(lambda v: f"{v:.1f}%"), textposition="outside"
            ))
            _fig_sit.add_trace(go.Bar(
                name=f"Alvo: {label_target}", x=_sit["situation"], y=_sit["pct_xg_t"],
                marker_color=[_sit_colors.get(s, "#888") for s in _sit["situation"]],
                opacity=1.0,
                text=_sit["pct_xg_t"].apply(lambda v: f"{v:.1f}%"), textposition="outside"
            ))
            _fig_sit.update_layout(
                template="plotly_dark", height=310, barmode="group",
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                yaxis_title="% do xG Total"
            )
            st.plotly_chart(_fig_sit, use_container_width=True)

        with _c_sit2:
            st.markdown("##### 🎯 Qualidade do Chute (xG/chute) por Situação")
            _fig_sit2 = go.Figure()
            _fig_sit2.add_trace(go.Bar(
                name=f"Base: {label_base}", x=_sit["situation"], y=_sit["xg_per_shot_b"],
                marker_color="#00BFFF", opacity=0.75,
                text=_sit["xg_per_shot_b"].apply(lambda v: f"{v:.3f}" if pd.notnull(v) else "—"),
                textposition="outside"
            ))
            _fig_sit2.add_trace(go.Bar(
                name=f"Alvo: {label_target}", x=_sit["situation"], y=_sit["xg_per_shot_t"],
                marker_color="#00FF87",
                text=_sit["xg_per_shot_t"].apply(lambda v: f"{v:.3f}" if pd.notnull(v) else "—"),
                textposition="outside"
            ))
            _fig_sit2.update_layout(
                template="plotly_dark", height=310, barmode="group",
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                yaxis_title="xG médio por chute"
            )
            st.plotly_chart(_fig_sit2, use_container_width=True)

        # Tabela resumo de situações
        _sit_disp = _sit.rename(columns={
            "situation": "Situação",
            "shots_b": f"Chutes ({label_base})", "shots_t": f"Chutes ({label_target})",
            "xg_b": f"xG ({label_base})", "xg_t": f"xG ({label_target})",
            "pct_xg_b": f"% xG ({label_base})", "pct_xg_t": f"% xG ({label_target})",
            "xg_per_shot_b": f"xG/Chute ({label_base})", "xg_per_shot_t": f"xG/Chute ({label_target})",
        })[["Situação", f"Chutes ({label_base})", f"Chutes ({label_target})",
             f"xG ({label_base})", f"xG ({label_target})",
             f"% xG ({label_base})", f"% xG ({label_target})",
             f"xG/Chute ({label_base})", f"xG/Chute ({label_target})"]].copy()

        with st.expander("📋 Tabela Completa: Situação Tática × Métricas"):
            st.dataframe(
                _sit_disp.style.format({
                    f"xG ({label_base})": "{:.2f}", f"xG ({label_target})": "{:.2f}",
                    f"% xG ({label_base})": "{:.1f}%", f"% xG ({label_target})": "{:.1f}%",
                    f"xG/Chute ({label_base})": "{:.3f}", f"xG/Chute ({label_target})": "{:.3f}",
                }),
                use_container_width=True, hide_index=True
            )

    # =========================================================================
    # NOVA SEÇÃO C — SCOUT REPORT NARRATIVO AUTOMÁTICO
    # =========================================================================
    # Pre-compute shot profile & goalkeeper vars needed by Scout Report
    # (these are also computed in section 3.1 below — keeping both is harmless)
    dist_b = s_base["distance_meters"].mean() if not s_base.empty and "distance_meters" in s_base.columns else 0.0
    dist_t = s_target["distance_meters"].mean() if not s_target.empty and "distance_meters" in s_target.columns else 0.0
    box_b = (s_base["distance_meters"] <= 16.5).mean() * 100 if not s_base.empty and "distance_meters" in s_base.columns else 0.0
    box_t = (s_target["distance_meters"] <= 16.5).mean() * 100 if not s_target.empty and "distance_meters" in s_target.columns else 0.0
    xg_shot_b = s_base["xg"].mean() if not s_base.empty else 0.0
    xg_shot_t = s_target["xg"].mean() if not s_target.empty else 0.0
    opp_gp_b = m_base["opponent_goals_prevented"].sum() if "opponent_goals_prevented" in m_base.columns else 0.0
    opp_gp_t = m_target["opponent_goals_prevented"].sum() if "opponent_goals_prevented" in m_target.columns else 0.0
    opp_gp_per_m_b = opp_gp_b / n_m_base if n_m_base > 0 else 0.0
    opp_gp_per_m_t = opp_gp_t / n_m_target if n_m_target > 0 else 0.0

    st.markdown("---")
    with st.expander("📝 Diagnóstico Técnico Completo — Scout Report Automático", expanded=False):
        st.caption("Relatório editorial gerado automaticamente com base nos dados do período comparado. Estilo análise técnica de scout profissional.")

        # Decomposição fatorial waterfall: ΔxG/90 = ΔV × Q_base + V_base × ΔQ + ΔV × ΔQ
        _v_base_shot = v_base  # shots/game base
        _v_target_shot = v_target  # shots/game target
        _q_base = xg_total_b / max(1, n_s_base)  # xG/shot base
        _q_target = xg_total_t / max(1, n_s_target)  # xG/shot target
        _delta_v = _v_target_shot - _v_base_shot
        _delta_q = _q_target - _q_base
        _effect_vol = _delta_v * _q_base   # efeito volume
        _effect_qual = _v_base_shot * _delta_q  # efeito qualidade
        _effect_cross = _delta_v * _delta_q  # efeito cruzado
        _total_delta = _effect_vol + _effect_qual + _effect_cross

        # Dominant effect
        if abs(_effect_vol) > abs(_effect_qual):
            _dom_effect = f"**Efeito Volume** ({_effect_vol:+.2f} xG/j — {abs(_effect_vol/max(0.001,abs(_total_delta)))*100:.0f}% do delta)"
            _dom_msg = f"a mudança decorreu principalmente de {'mais' if _delta_v > 0 else 'menos'} finalizações por jogo ({_v_base_shot:.1f} → {_v_target_shot:.1f} chutes/j)"
        else:
            _dom_effect = f"**Efeito Qualidade** ({_effect_qual:+.2f} xG/j — {abs(_effect_qual/max(0.001,abs(_total_delta)))*100:.0f}% do delta)"
            _dom_msg = f"a mudança decorreu de {'melhores' if _delta_q > 0 else 'piores'} posições de finalização ({_q_base:.3f} → {_q_target:.3f} xG/chute)"

        _report_lines = [
            f"### Palmeiras: {label_base} → {label_target}",
            "",
            f"**Síntese ofensiva:** No período **{label_target}**, o Palmeiras produziu **{xg90_target:.2f} xG/jogo** "
            f"({'acima' if xg90_target >= xg90_base else 'abaixo'} dos {xg90_base:.2f} de {label_base}, delta: {delta_xg:+.2f} xG/j). "
            f"Em termos de gols reais, a equipe marcou **{gp90_t:.2f}/j** (base: {gp90_b:.2f}/j, Δ: {delta_gp:+.2f}).",
            "",
            f"**Decomposição fatorial do ΔxG/90 = {_total_delta:+.2f}:**",
            f"- Efeito Volume: {_effect_vol:+.3f} xG/j (chutar mais/menos — {_v_base_shot:.1f}→{_v_target_shot:.1f} chutes/j)",
            f"- Efeito Qualidade: {_effect_qual:+.3f} xG/j (posições melhores/piores — {_q_base:.3f}→{_q_target:.3f} xG/chute)",
            f"- Efeito Cruzado: {_effect_cross:+.3f} xG/j",
            f"- **Fator dominante:** {_dom_effect} — {_dom_msg}.",
            "",
            f"**Perfil espacial:** Distância média de finalização: {dist_b:.1f}m ({label_base}) → {dist_t:.1f}m ({label_target}) "
            f"({'aproximação' if dist_t < dist_b else 'recuo'} de {abs(dist_t - dist_b):.1f}m). "
            f"Chutes de dentro da área: {box_b:.1f}% → {box_t:.1f}% "
            f"({'↑ maior penetração' if box_t > box_b else '↓ menor penetração'}).",
            "",
            f"**Solidez defensiva:** xG concedido passou de **{xgc90_b:.2f}/j** para **{xgc90_t:.2f}/j** "
            f"(Δ: {delta_xgc:+.2f}). Gols sofridos: {gc90_b:.2f}/j → {gc90_t:.2f}/j. "
            f"{'A zaga melhorou a blindagem defensiva.' if delta_xgc < -0.1 else ('A exposição defensiva aumentou.' if delta_xgc > 0.1 else 'A solidez defensiva se manteve estável.')}",
            "",
            f"**Goleiros adversários:** Gols evitados pelos goleiros rivais: {opp_gp_per_m_b:+.2f}/j ({label_base}) → "
            f"{opp_gp_per_m_t:+.2f}/j ({label_target}). "
            f"{'Goleiros rivais foram mais determinantes no período alvo.' if opp_gp_per_m_t > opp_gp_per_m_b + 0.15 else ('Goleiros rivais foram menos decisivos no período alvo.' if opp_gp_per_m_t < opp_gp_per_m_b - 0.15 else 'Impacto dos goleiros rivais similar entre os períodos.')}",
            "",
            f"**Aproveitamento:** {aprov_b:.1f}% → {aprov_t:.1f}% (Δ: {delta_aprov:+.1f}pp). "
            f"{'Evolução de resultados consistente com a melhora analítica.' if delta_aprov > 0 and delta_xg >= 0 else ('Queda de resultados consistente com recuo analítico.' if delta_aprov < 0 and delta_xg < 0 else 'Discrepância entre aproveitamento e criação — possível influência de variância de conversão.')}",
        ]

        st.markdown("\n".join(_report_lines))
        st.caption(f"📌 Relatório gerado automaticamente | Base: SofaScore API | Palmeiras xG Analytics")

    # =========================================================================
    # SEÇÃO 3.1 — INVESTIGAÇÃO CAUSAL DA LETALIDADE / CONVERSÃO (original)
    # =========================================================================
    # -------------------------------------------------------------------------
    # 3.1 INVESTIGAÇÃO CAUSAL DA LETALIDADE / CONVERSÃO
    # -------------------------------------------------------------------------
    st.markdown("##### 🔬 Raio-X da Mudança no Ataque: Por que a Bola Parou de Entrar?")
    st.caption("Três respostas visuais e diretas nos dados: os goleiros rivais pegaram tudo? O time chutou pior? Ou os atacantes perderam a pontaria?")

    # 1. Goleiros adversários
    opp_gp_b = m_base["opponent_goals_prevented"].sum() if "opponent_goals_prevented" in m_base.columns else 0.0
    opp_gp_t = m_target["opponent_goals_prevented"].sum() if "opponent_goals_prevented" in m_target.columns else 0.0
    opp_gp_per_m_b = opp_gp_b / n_m_base if n_m_base > 0 else 0.0
    opp_gp_per_m_t = opp_gp_t / n_m_target if n_m_target > 0 else 0.0
    delta_opp_gp = opp_gp_t - opp_gp_b

    # 2. Perfil das finalizações
    dist_b = s_base["distance_meters"].mean() if not s_base.empty and "distance_meters" in s_base.columns else 0.0
    dist_t = s_target["distance_meters"].mean() if not s_target.empty and "distance_meters" in s_target.columns else 0.0
    box_b = (s_base["distance_meters"] <= 16.5).mean() * 100 if not s_base.empty and "distance_meters" in s_base.columns else 0.0
    box_t = (s_target["distance_meters"] <= 16.5).mean() * 100 if not s_target.empty and "distance_meters" in s_target.columns else 0.0
    xg_shot_b = s_base["xg"].mean() if not s_base.empty else 0.0
    xg_shot_t = s_target["xg"].mean() if not s_target.empty else 0.0

    # 3. Regressão individual de conversão
    pb_leth = s_base.groupby("player_name").agg(xg_b=("xg", "sum"), gols_b=("is_goal", "sum"), ch_b=("shot_id", "count")).reset_index()
    pt_leth = s_target.groupby("player_name").agg(xg_t=("xg", "sum"), gols_t=("is_goal", "sum"), ch_t=("shot_id", "count")).reset_index()
    pm_leth = pd.merge(pb_leth, pt_leth, on="player_name", how="outer").fillna(0)
    pm_leth["diff_b"] = pm_leth["gols_b"] - pm_leth["xg_b"]
    pm_leth["diff_t"] = pm_leth["gols_t"] - pm_leth["xg_t"]
    pm_leth["delta_eff"] = pm_leth["diff_t"] - pm_leth["diff_b"]

    # Tratamento de atletas transferidos (ex: Allan)
    DEPARTED_PLAYERS = ["Allan"]
    col_filter_row, _ = st.columns([1.6, 2.4])
    with col_filter_row:
        excluir_transferidos = st.checkbox("Focar no elenco ativo (desconsiderar atletas negociados como Allan)", value=True, key="chk_vendidos")

    if excluir_transferidos:
        pm_leth_active = pm_leth[~pm_leth["player_name"].isin(DEPARTED_PLAYERS)].copy()
    else:
        pm_leth_active = pm_leth.copy()

    top_fallers = pm_leth_active.sort_values(by="delta_eff", ascending=True).head(4)
    top_gainers = pm_leth_active.sort_values(by="delta_eff", ascending=False).head(4)

    # Nota sobre Allan
    allan_row = pm_leth[pm_leth["player_name"] == "Allan"]
    allan_note = ""
    if not allan_row.empty:
        allan_delta = allan_row.iloc[0]["delta_eff"]
        allan_note = f"<div style='color: #F59E0B; font-size: 0.74rem; margin-top: 4px;'>ℹ️ Nota: Allan teve oscilação de {allan_delta:+.2f} gols vs xG antes de ser negociado.</div>"

    inv_c1, inv_c2, inv_c3 = st.columns(3)
    with inv_c1:
        st.markdown(
            f"""
            <div style="background-color: #1A2430; border: 1px solid #00BFFF; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase;">🧤 Goleiros Rivais: Fecharam o Gol?</div>
                <div style="color: {'#FF4B4B' if opp_gp_per_m_t > 0 else '#00FF87'}; font-size: 1.4rem; font-weight: bold; margin: 4px 0;">{opp_gp_per_m_t:+.2f} gols salvos / jogo</div>
                <div style="color: #CBD5E1; font-size: 0.78rem; margin-bottom: 6px;">Total no período: {opp_gp_t:+.2f} gols acumulados (vs {opp_gp_b:+.2f} na base)</div>
                <div style="color: #94A3B8; font-size: 0.74rem; border-top: 1px solid #2A3B50; padding-top: 6px; text-align: left; line-height: 1.35;">
                    📖 <b>De onde sai:</b> Calculado pelo perigo real dos chutes no alvo (xGOT) menos os gols sofridos pelo rival. Em <b>{label_base}</b>, o saldo foi {opp_gp_per_m_b:+.2f} gols/j. Em <b>{label_target}</b>, foi {opp_gp_per_m_t:+.2f} gols/j. {'🔺 Goleiros rivais melhoraram consideravelmente.' if opp_gp_per_m_t > opp_gp_per_m_b + 0.2 else ('🔻 Goleiros rivais foram menos decisivos.' if opp_gp_per_m_t < opp_gp_per_m_b - 0.2 else '↔️ Desempenho dos goleiros rivais foi similar.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with inv_c2:
        st.markdown(
            f"""
            <div style="background-color: #1A2430; border: 1px solid #00BFFF; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase;">📍 Onde o Time Chutou? (Distância & Área)</div>
                <div style="color: #00FF87; font-size: 1.4rem; font-weight: bold; margin: 4px 0;">{dist_t:.1f} metros <span style="font-size: 0.85rem; color: #94A3B8;">({box_t:.1f}% na área)</span></div>
                <div style="color: #CBD5E1; font-size: 0.78rem; margin-bottom: 6px;">Base: {dist_b:.1f}m ({box_b:.1f}% na área) • xG/chute: {xg_shot_t:.2f} (base: {xg_shot_b:.2f})</div>
                <div style="color: #94A3B8; font-size: 0.74rem; border-top: 1px solid #2A3B50; padding-top: 6px; text-align: left; line-height: 1.35;">
                    📖 <b>O que significa:</b> Mostra se o ataque passou a arrematar de longe. Em <b>{label_base}</b>: {dist_b:.1f}m de distância média, {box_b:.1f}% na área. Em <b>{label_target}</b>: {dist_t:.1f}m, {box_t:.1f}% na área. {'✅ Chutes migraram para posições mais perigosas.' if dist_t < dist_b - 0.5 or box_t > box_b + 2 else ('⚠️ Chutes migraram para posições mais distantes.' if dist_t > dist_b + 0.5 or box_t < box_b - 2 else '↔️ Perfil espacial de finalização similar entre os períodos.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with inv_c3:
        faller_txt = top_fallers.iloc[0]['player_name'] if not top_fallers.empty else "Nenhum"
        faller_delta = top_fallers.iloc[0]['delta_eff'] if not top_fallers.empty else 0
        faller_desc = ""
        if not top_fallers.empty:
            r0 = top_fallers.iloc[0]
            faller_desc = f"{int(r0['gols_t'])}G em {r0['xg_t']:.2f}xG no alvo (vs {int(r0['gols_b'])}G em {r0['xg_b']:.2f}xG)"

        st.markdown(
            f"""
            <div style="background-color: #1A2430; border: 1px solid #00BFFF; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase;">📉 Maior Queda de Eficiência (Elenco Ativo)</div>
                <div style="color: #FF4B4B; font-size: 1.4rem; font-weight: bold; margin: 4px 0;">{faller_txt}</div>
                <div style="color: #CBD5E1; font-size: 0.78rem; margin-bottom: 6px;">Queda: {faller_delta:+.2f} gols vs. expectativa ({faller_desc})</div>
                <div style="color: #94A3B8; font-size: 0.74rem; border-top: 1px solid #2A3B50; padding-top: 6px; text-align: left; line-height: 1.35;">
                    📖 <b>De onde sai:</b> Em <b>{label_base}</b>: {top_fallers.iloc[0]['diff_b']:+.2f} gols vs xG. Em <b>{label_target}</b>: {top_fallers.iloc[0]['diff_t']:+.2f} gols vs xG. Diferença: {faller_delta:+.2f} gols {'a menos' if faller_delta < 0 else 'a mais'} em relação à expectativa.
                </div>
                {allan_note}
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3 GRÁFICOS VISUAIS EXPLICATIVOS
    st.markdown("##### 📊 Decomposição Visual da Mudança de Rendimento")
    st.caption("Três visões gráficas demonstrando exatamente os fatores que causaram a oscilação de gols.")

    col_g1, col_g2, col_g3 = st.columns(3)

    with col_g1:
        st.markdown("###### 1. Atuação dos Goleiros Rivais: Fecharam o Gol?")
        st.caption("Chutes no alvo com endereço de gol vs. Gols sofridos pelo rival.")
        xgot_b = s_base["xgot"].dropna().sum() if not s_base.empty else 0.0
        xgot_t = s_target["xgot"].dropna().sum() if not s_target.empty else 0.0
        gols_b_tot = s_base["is_goal"].sum() if not s_base.empty else 0
        gols_t_tot = s_target["is_goal"].sum() if not s_target.empty else 0

        fig_muralha = go.Figure()
        fig_muralha.add_trace(go.Bar(
            x=[label_base, label_target], y=[round(xgot_b, 1), round(xgot_t, 1)],
            name="Chutes no Gol (Gols Prováveis)", marker_color="#00BFFF",
            text=[f"{xgot_b:.1f}", f"{xgot_t:.1f}"], textposition="outside"
        ))
        fig_muralha.add_trace(go.Bar(
            x=[label_base, label_target], y=[gols_b_tot, gols_t_tot],
            name="Gols Sofridos pelo Rival", marker_color="#FF4B4B",
            text=[str(gols_b_tot), str(gols_t_tot)], textposition="outside"
        ))
        fig_muralha.update_layout(
            template="plotly_dark", height=280, barmode="group",
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_muralha, use_container_width=True)
        st.caption(f"💡 No 1ºT, rivais falharam (levaram {gols_b_tot - xgot_b:+.1f} gols a mais). No 2ºT, fecharam o gol (salvaram {xgot_t - gols_t_tot:+.1f} gols certos).")

    with col_g2:
        st.markdown("###### 2. Seleção de Chutes: Chutou Mais de Perto ou de Longe?")
        st.caption("Mostra se a pontaria caiu porque o time se afobou chutando de longe.")
        fig_perfil = go.Figure()
        fig_perfil.add_trace(go.Bar(
            y=["Distância Média (m)", "% Chutes na Área", "Qualidade do Chute (xG x 100)"],
            x=[round(dist_b, 1), round(box_b, 1), round(xg_shot_b * 100, 1)],
            name=label_base, orientation="h", marker_color="#00BFFF",
            text=[f"{dist_b:.1f}m", f"{box_b:.1f}%", f"{xg_shot_b:.2f}"], textposition="outside"
        ))
        fig_perfil.add_trace(go.Bar(
            y=["Distância Média (m)", "% Chutes na Área", "Qualidade do Chute (xG x 100)"],
            x=[round(dist_t, 1), round(box_t, 1), round(xg_shot_t * 100, 1)],
            name=label_target, orientation="h", marker_color="#00FF87",
            text=[f"{dist_t:.1f}m", f"{box_t:.1f}%", f"{xg_shot_t:.2f}"], textposition="outside"
        ))
        fig_perfil.update_layout(
            template="plotly_dark", height=280, barmode="group",
            margin=dict(l=10, r=20, t=20, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_perfil, use_container_width=True)
        st.caption("💡 O time NÃO chutou de longe: a distância encurtou e os chutes na área subiram.")

    with col_g3:
        st.markdown("###### 3. Queda de Eficiência por Atacante")
        st.caption("Jogadores que converteram menos gols do que o xG previa (apenas quedas reais).")
        # Bug fix: filter only players with actual decline (delta_eff < 0), not abs() of all
        chart_fallers = pm_leth_active[pm_leth_active["delta_eff"] < 0].sort_values(by="delta_eff", ascending=True).head(4).copy()
        chart_fallers["gols_perdidos"] = chart_fallers["delta_eff"].abs()

        if chart_fallers.empty:
            st.info("✅ Nenhum atleta registrou queda real de eficiência. Todos mantiveram ou melhoraram a conversão.")
        else:
            hover_fallers = [
                f"<b>{r['player_name']}</b><br>{label_base}: {r['diff_b']:+.2f} vs xG ({int(r['gols_b'])}G em {r['xg_b']:.2f} xG)<br>{label_target}: {r['diff_t']:+.2f} vs xG ({int(r['gols_t'])}G em {r['xg_t']:.2f} xG)<br><b>Queda: {r['gols_perdidos']:.2f} gols perdidos</b>"
                for _, r in chart_fallers.iterrows()
            ]

            fig_regress = go.Figure()
            fig_regress.add_trace(go.Bar(
                y=chart_fallers["player_name"],
                x=chart_fallers["gols_perdidos"],
                orientation="h",
                marker_color="#FF4B4B",
                text=[f"-{d:.2f} gols" for d in chart_fallers["gols_perdidos"]],
                textposition="outside",
                hovertext=hover_fallers,
                hoverinfo="text"
            ))
            fig_regress.update_layout(
                template="plotly_dark", height=280,
                margin=dict(l=10, r=25, t=20, b=10),
                yaxis=dict(categoryorder="total ascending"),
                xaxis=dict(title="Gols Perdidos vs. Expectativa xG", range=[0, max(chart_fallers["gols_perdidos"].max() * 1.4, 1.0)], dtick=0.5)
            )
            st.plotly_chart(fig_regress, use_container_width=True)
            # Dynamic caption using actual computed values
            top_faller_row = chart_fallers.iloc[0]
            st.caption(
                f"📖 <b>Fórmula:</b> (Gols {label_target} − xG {label_target}) menos (Gols {label_base} − xG {label_base}). "
                f"<b>{top_faller_row['player_name']}</b>, por exemplo: "
                f"{label_base}: {top_faller_row['diff_b']:+.2f} vs xG → {label_target}: {top_faller_row['diff_t']:+.2f} vs xG "
                f"(queda de {top_faller_row['gols_perdidos']:.2f} gols vs expectativa).",
                unsafe_allow_html=True
            )

    # Síntese Executiva Final — totalmente dinâmica, condicional ao resultado
    _fallers_names = ", ".join(chart_fallers["player_name"].tolist()[:3]) if not chart_fallers.empty else "nenhum atleta"
    _gainers_eff = pm_leth_active[pm_leth_active["delta_eff"] > 0].sort_values("delta_eff", ascending=False)
    _gainers_names = ", ".join(_gainers_eff["player_name"].tolist()[:2]) if not _gainers_eff.empty else "nenhum atleta"

    if delta_gp > 0.15:  # gols pró subiram
        _gols_txt = (
            f"O salto de <b>{delta_gp:+.2f} gols/j</b> ({label_base} → {label_target}) foi impulsionado por "
            f"<b>(1) aumento real na criação de perigo</b> (xG/90: {xg90_base:.2f} → {xg90_target:.2f}) e "
            f"<b>(2) maior conversão</b> de atacantes como <b>{_gainers_names}</b>. "
            f"{'Os goleiros rivais foram menos determinantes neste período.' if (opp_gp_per_m_t < opp_gp_per_m_b - 0.2) else ''}"
        )
    elif delta_gp < -0.15:  # gols pró caíram
        _gols_txt = (
            f"A queda de <b>{abs(delta_gp):.2f} gols/j</b> ({label_base} → {label_target}) decorreu de "
            f"<b>(1) goleiros adversários mais decisivos</b> ({opp_gp_per_m_t:+.2f} gols salvos/j no período alvo) e "
            f"<b>(2) regressão à média de {_fallers_names}</b>, que viviam conversão insustentável. "
            f"{'O time não piorou a qualidade da criação (xG/90 mantido em ' + f'{xg90_target:.2f}).' if abs(delta_xg) < 0.15 else 'A criação também recuou (xG/90: ' + f'{xg90_base:.2f} → {xg90_target:.2f}).'}"
        )
    else:  # estável
        _gols_txt = (
            f"O rendimento ofensivo se manteve estável entre <b>{label_base}</b> e <b>{label_target}</b> "
            f"(xG/90: {xg90_base:.2f} → {xg90_target:.2f} | Gols/j: {gp90_b:.2f} → {gp90_t:.2f}). "
            f"{'Pequenas oscilações de conversão individual foram compensadas coletivamente.' if chart_fallers.empty or _gainers_eff.empty else f'Oscilações individuais se equilibraram: {_fallers_names} recuaram em conversão, mas {_gainers_names} compensaram.'}"
        )

    _border_color = "#00FF87" if delta_gp >= 0 else "#FF4B4B"
    st.markdown(
        f"""
        <div style="background-color: #0e1e28; border-left: 4px solid {_border_color}; border-radius: 4px; padding: 12px 18px; margin-top: 10px; margin-bottom: 20px;">
            <div style="color: {_border_color}; font-weight: bold; font-size: 0.92rem; margin-bottom: 4px;">💡 Conclusão da Investigação ({label_base} → {label_target}):</div>
            <div style="color: #E2E8F0; font-size: 0.88rem; line-height: 1.5;">
                {_gols_txt}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 4. PROTAGONISTAS: QUEM GANHOU E QUEM PERDEU RENDIMENTO
    # -------------------------------------------------------------------------
    st.markdown("#### 🧩 Protagonistas Ofensivos: Quem Melhorou e Quem Piorou?")
    st.caption("Descubra os jogadores responsáveis pelas oscilações de criação e conversão.")

    pb = s_base.groupby("player_name").agg(
        xg_b=("xg", "sum"), gols_b=("is_goal", "sum"), chutes_b=("shot_id", "count")
    ).reset_index()

    pt = s_target.groupby("player_name").agg(
        xg_t=("xg", "sum"), gols_t=("is_goal", "sum"), chutes_t=("shot_id", "count")
    ).reset_index()

    pm = pd.merge(pb, pt, on="player_name", how="outer").fillna(0)
    pm["delta_xg"] = (pm["xg_t"] - pm["xg_b"]).round(2)
    pm["delta_gols"] = (pm["gols_t"] - pm["gols_b"]).astype(int)
    pm["diff_eff_b"] = (pm["gols_b"] - pm["xg_b"]).round(2)
    pm["diff_eff_t"] = (pm["gols_t"] - pm["xg_t"]).round(2)
    pm["delta_eff"] = (pm["diff_eff_t"] - pm["diff_eff_b"]).round(2)
    pm["xg_total_ambos"] = pm["xg_b"] + pm["xg_t"]
    pm["chutes_total"] = pm["chutes_b"] + pm["chutes_t"]
    pm["gols_total"] = pm["gols_b"] + pm["gols_t"]

    top_players = pm[pm["chutes_total"] >= 3].sort_values(by="xg_total_ambos", ascending=False).copy()

    # Destaques em Cards
    if not top_players.empty:
        # Se o usuário marcou para excluir transferidos (Allan), filtramos aqui também
        pm_cards = pm[~pm["player_name"].isin(DEPARTED_PLAYERS)].copy() if excluir_transferidos else pm.copy()

        most_growth_xg = pm_cards.sort_values(by="delta_xg", ascending=False).iloc[0]
        most_drop_xg = pm_cards.sort_values(by="delta_xg", ascending=True).iloc[0]
        scorers = pm_cards[pm_cards["gols_total"] >= 2].sort_values(by="delta_gols", ascending=False)
        most_growth_gols = scorers.iloc[0] if not scorers.empty else pm_cards.sort_values(by="delta_gols", ascending=False).iloc[0]

        cd1, cd2, cd3 = st.columns(3)
        with cd1:
            st.markdown(
                f"""
                <div style="background-color: #122416; border: 1.5px solid #00FF87; border-radius: 8px; padding: 14px; height: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="color: #94A3B8; font-size: 0.78rem; text-transform: uppercase; font-weight: bold;">🚀 Maior Salto em Criação (xG)</span>
                        <span style="background-color: #1E3A24; color: #00FF87; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">{most_growth_xg['delta_xg']:+.2f} xG</span>
                    </div>
                    <div style="color: #FFFFFF; font-size: 1.35rem; font-weight: bold; margin-bottom: 4px;">{most_growth_xg['player_name']}</div>
                    <div style="color: #A7F3D0; font-size: 0.85rem; margin-bottom: 8px;">
                        Gerou <b>{most_growth_xg['xg_t']:.2f} xG</b> no período (vs {most_growth_xg['xg_b']:.2f} na base)
                    </div>
                    <div style="color: #CBD5E1; font-size: 0.78rem; border-top: 1px solid #1E3A24; padding-top: 8px; line-height: 1.4;">
                        💡 <b>O que significa:</b> Atacante que mais ampliou o perigo gerado em campo, finalizando em posições de maior probabilidade de gol graças à movimentação e criação coletiva.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with cd2:
            st.markdown(
                f"""
                <div style="background-color: #122416; border: 1.5px solid #00FF87; border-radius: 8px; padding: 14px; height: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="color: #94A3B8; font-size: 0.78rem; text-transform: uppercase; font-weight: bold;">🎯 Maior Salto em Gols Reais</span>
                        <span style="background-color: #1E3A24; color: #00FF87; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">{most_growth_gols['delta_gols']:+d} gols</span>
                    </div>
                    <div style="color: #FFFFFF; font-size: 1.35rem; font-weight: bold; margin-bottom: 4px;">{most_growth_gols['player_name']}</div>
                    <div style="color: #A7F3D0; font-size: 0.85rem; margin-bottom: 8px;">
                        Marcou <b>{int(most_growth_gols['gols_t'])} gols</b> no período (vs {int(most_growth_gols['gols_b'])} na base)
                    </div>
                    <div style="color: #CBD5E1; font-size: 0.78rem; border-top: 1px solid #1E3A24; padding-top: 8px; line-height: 1.4;">
                        💡 <b>O que significa:</b> Finalizador que mais colocou a bola na rede efetivamente, convertendo oportunidades em pontos reais conquistados na tabela.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with cd3:
            st.markdown(
                f"""
                <div style="background-color: #261618; border: 1.5px solid #FF4B4B; border-radius: 8px; padding: 14px; height: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="color: #94A3B8; font-size: 0.78rem; text-transform: uppercase; font-weight: bold;">📉 Maior Queda de Produção (xG)</span>
                        <span style="background-color: #3F1B1F; color: #FF4B4B; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">{most_drop_xg['delta_xg']:+.2f} xG</span>
                    </div>
                    <div style="color: #FFFFFF; font-size: 1.35rem; font-weight: bold; margin-bottom: 4px;">{most_drop_xg['player_name']}</div>
                    <div style="color: #FECDD3; font-size: 0.85rem; margin-bottom: 8px;">
                        Produziu <b>{most_drop_xg['xg_t']:.2f} xG</b> no período (vs {most_drop_xg['xg_b']:.2f} na base)
                    </div>
                    <div style="color: #CBD5E1; font-size: 0.78rem; border-top: 1px solid #3F1B1F; padding-top: 8px; line-height: 1.4;">
                        💡 <b>O que significa:</b> Redução de volume ou arremates efetuados em zonas menos favoráveis, sinalizando menor acionamento ou marcação mais ajustada dos adversários.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")

    col_div, col_scat = st.columns([1.1, 1.1])

    with col_div:
        st.markdown("##### 1. Divergência de Conversão Comparativa (G - xG)")
        st.caption("Compara a letalidade de cada atleta entre a Base (azul) e o Alvo (verde). Valores 100% alinhados.")

        eff_candidates = top_players.head(8).copy()
        if not eff_candidates.empty:
            fig_diverg = go.Figure()
            fig_diverg.add_trace(go.Bar(
                y=eff_candidates["player_name"],
                x=eff_candidates["diff_eff_b"],
                name=f"Base: {label_base}",
                orientation="h",
                marker_color="#00BFFF",
                text=eff_candidates["diff_eff_b"].apply(lambda v: f"{v:+.2f}"),
                textposition="outside"
            ))
            fig_diverg.add_trace(go.Bar(
                y=eff_candidates["player_name"],
                x=eff_candidates["diff_eff_t"],
                name=f"Alvo: {label_target}",
                orientation="h",
                marker_color="#00FF87",
                text=eff_candidates["diff_eff_t"].apply(lambda v: f"{v:+.2f}"),
                textposition="outside"
            ))
            fig_diverg.add_vline(x=0, line_color="#888888", line_width=1.5)
            fig_diverg.update_layout(
                template="plotly_dark", height=380, barmode="group",
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                yaxis=dict(categoryorder="total ascending")
            )
            st.plotly_chart(fig_diverg, use_container_width=True)
        else:
            st.info("Amostra pequena para comparação individual de conversão.")

    with col_scat:
        st.markdown("##### 2. Mapa de Eficiência dos Finalizadores (xG vs. Gols)")
        st.caption("Acima da linha diagonal tracejada = finalização clínica. Abaixo = underperformance.")

        scat_list = []
        for _, r in top_players.iterrows():
            if r["chutes_b"] >= 2:
                scat_list.append({"Atleta": r["player_name"], "xG": r["xg_b"], "Gols": r["gols_b"], "Chutes": r["chutes_b"], "Período": f"Base: {label_base}"})
            if r["chutes_t"] >= 2:
                scat_list.append({"Atleta": r["player_name"], "xG": r["xg_t"], "Gols": r["gols_t"], "Chutes": r["chutes_t"], "Período": f"Alvo: {label_target}"})
        scat_df = pd.DataFrame(scat_list)

        if not scat_df.empty:
            max_x = max(scat_df["xG"].max() * 1.15, 1.5)
            max_y = max(scat_df["Gols"].max() * 1.15, 2.0)
            diag_limit = min(max_x, max_y)

            destaques = top_players.head(4)["player_name"].tolist()
            scat_df["Rotulo"] = scat_df.apply(lambda row: row["Atleta"] if row["Atleta"] in destaques else "", axis=1)

            fig_scat_fin = px.scatter(
                scat_df, x="xG", y="Gols", size="Chutes", color="Período",
                text="Rotulo",
                hover_data={"Atleta": True, "Período": True, "xG": ":.2f", "Gols": True, "Chutes": True, "Rotulo": False},
                color_discrete_map={f"Base: {label_base}": "#00BFFF", f"Alvo: {label_target}": "#00FF87"},
                template="plotly_dark"
            )
            fig_scat_fin.add_trace(go.Scatter(
                x=[0, diag_limit], y=[0, diag_limit], mode="lines",
                name="Paridade (G = xG)",
                line=dict(color="#777777", dash="dash", width=1.5)
            ))
            fig_scat_fin.update_traces(textposition="top center")
            fig_scat_fin.update_layout(
                template="plotly_dark", height=380,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis=dict(title="Gols Esperados (xG Acumulado)", range=[0, max_x]),
                yaxis=dict(title="Gols Reais Marcados", range=[0, max_y]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_scat_fin, use_container_width=True)

    st.markdown("---")

    # Tabela Completa de Deltas
    st.markdown("##### 3. Balanço Completo da Evolução dos Jogadores (Deltas)")
    st.caption("Verde = evolução positiva; Vermelho = queda de produção. Ordenado por volume de chances.")

    disp_df = top_players[[
        "player_name", "xg_b", "xg_t", "delta_xg", "gols_b", "gols_t", "delta_gols", "diff_eff_b", "diff_eff_t"
    ]].copy().rename(columns={
        "player_name": "Atleta",
        "xg_b": f"xG ({label_base})",
        "xg_t": f"xG ({label_target})",
        "delta_xg": "Δ xG",
        "gols_b": f"Gols ({label_base})",
        "gols_t": f"Gols ({label_target})",
        "delta_gols": "Δ Gols",
        "diff_eff_b": f"Letalidade ({label_base})",
        "diff_eff_t": f"Letalidade ({label_target})"
    })

    def style_deltas(val):
        try:
            v = float(val)
            if v > 0.05:
                return "color: #00FF87; font-weight: bold;"
            elif v < -0.05:
                return "color: #FF4B4B; font-weight: bold;"
        except:
            pass
        return ""

    styled_table = disp_df.head(15).style.format({
        f"xG ({label_base})": "{:.2f}",
        f"xG ({label_target})": "{:.2f}",
        "Δ xG": "{:+.2f}",
        "Δ Gols": "{:+d}",
        f"Letalidade ({label_base})": "{:+.2f}",
        f"Letalidade ({label_target})": "{:+.2f}"
    })
    styler_map = getattr(styled_table, "map", getattr(styled_table, "applymap", None))
    if styler_map is not None:
        styled_table = styler_map(style_deltas, subset=["Δ xG", "Δ Gols", f"Letalidade ({label_base})", f"Letalidade ({label_target})"])

    st.dataframe(styled_table, use_container_width=True, hide_index=True)

    # =========================================================================
    # NOVA SEÇÃO D — SHOTMAP COMPARATIVO POR JOGADOR
    # =========================================================================
    st.markdown("---")
    st.markdown("#### 🗺️ Mapa de Chutes Comparativo por Jogador")
    st.caption(
        "Selecione um atleta e veja lado a lado onde ele finalizou em cada período. "
        "Responde: as posições de finalização mudaram entre os períodos comparados?"
    )

    _eligible = top_players[top_players["chutes_total"] >= 4]["player_name"].tolist()
    if _eligible:
        _sel_player = st.selectbox(
            "Selecione o Atleta:", _eligible, key="v2_shotmap_player_sel",
            help="Apenas atletas com ≥ 4 finalizações nos dois períodos combinados."
        )

        _shots_b_player = s_base[s_base["player_name"] == _sel_player].copy()
        _shots_t_player = s_target[s_target["player_name"] == _sel_player].copy()

        _n_b = len(_shots_b_player)
        _n_t = len(_shots_t_player)
        _xg_b_p = _shots_b_player["xg"].sum()
        _xg_t_p = _shots_t_player["xg"].sum()
        _g_b_p = int(_shots_b_player["is_goal"].sum())
        _g_t_p = int(_shots_t_player["is_goal"].sum())

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from mplsoccer import VerticalPitch

            _outcome_colors = {
                "Gol": "#00FF87", "Defesa": "#00BFFF",
                "Para Fora": "#FF4B4B", "Bloqueado": "#FFA500", "Trave": "#FFD700"
            }

            fig_cmp, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 7), facecolor="#0e1117")
            pitch = VerticalPitch(pitch_type="custom", pitch_length=105, pitch_width=68,
                                  pitch_color="#0e1117", line_color="#ffffff66",
                                  half=True, pad_top=2)

            for ax, _shots_p, period_label, n_shots, xg_p, g_p in [
                (ax1, _shots_b_player, label_base, _n_b, _xg_b_p, _g_b_p),
                (ax2, _shots_t_player, label_target, _n_t, _xg_t_p, _g_t_p),
            ]:
                pitch.draw(ax=ax)
                ax.set_title(
                    f"{period_label}\n{n_shots} chutes | {xg_p:.2f} xG | {g_p} gols",
                    color="#E2E8F0", fontsize=10, pad=8, fontweight="bold"
                )
                if not _shots_p.empty and "x_pct" in _shots_p.columns:
                    _sp = _shots_p.copy()
                    _sp["pitch_x"] = 105.0 - (_sp["x_pct"] * 1.05)
                    _sp["pitch_y"] = (1.0 - _sp["y_pct"] / 100.0) * 68.0
                    _sp["sz"] = np.clip(np.sqrt(_sp["xg"]) * 380, 40, 360)
                    for outcome, col in _outcome_colors.items():
                        _sub = _sp[_sp["outcome"] == outcome]
                        if _sub.empty:
                            continue
                        pitch.scatter(
                            _sub["pitch_x"], _sub["pitch_y"], ax=ax,
                            s=_sub["sz"], c=col, alpha=0.85,
                            edgecolors="white" if outcome == "Gol" else col,
                            linewidths=1.5 if outcome == "Gol" else 0.5,
                            label=outcome, zorder=5
                        )
                else:
                    ax.text(34, 78, "Sem dados\nespaciais", ha="center", va="center",
                            color="#94A3B8", fontsize=10)

            # Legend from first axis
            handles = [plt.Line2D([0], [0], marker='o', color='w',
                                  markerfacecolor=c, markersize=9, label=o)
                       for o, c in _outcome_colors.items()]
            fig_cmp.legend(handles=handles, loc="lower center", ncol=5,
                           facecolor="#0e1117", edgecolor="#2d3a56", labelcolor="#E2E8F0",
                           fontsize=9, framealpha=0.9, bbox_to_anchor=(0.5, 0.02))
            fig_cmp.suptitle(
                f"Distribuição Espacial de Finalizações — {_sel_player}",
                color="#00FF87", fontsize=13, fontweight="bold", y=0.98
            )
            plt.tight_layout(rect=[0, 0.06, 1, 0.96])
            st.pyplot(fig_cmp, use_container_width=True)
            plt.close(fig_cmp)

        except Exception as _e:
            st.warning(f"Não foi possível renderizar o shotmap comparativo: {_e}")

        # Player narrative
        _dist_b_p = _shots_b_player["distance_meters"].mean() if "distance_meters" in _shots_b_player.columns and not _shots_b_player.empty else 0
        _dist_t_p = _shots_t_player["distance_meters"].mean() if "distance_meters" in _shots_t_player.columns and not _shots_t_player.empty else 0
        _xg_shot_b_p = _xg_b_p / max(1, _n_b)
        _xg_shot_t_p = _xg_t_p / max(1, _n_t)
        st.markdown(
            f"""
            <div style="background:#1a2234; border:1px solid #2d3a56; border-radius:8px; padding:12px 16px; margin-top:8px; font-size:0.86rem; color:#E2E8F0; line-height:1.6;">
            <b style="color:#00FF87;">📊 {_sel_player} — Análise Comparativa</b><br>
            <b>{label_base}:</b> {_n_b} chutes | {_xg_b_p:.2f} xG | {_g_b_p} gols | xG/chute: {_xg_shot_b_p:.3f} | Distância: {_dist_b_p:.1f}m<br>
            <b>{label_target}:</b> {_n_t} chutes | {_xg_t_p:.2f} xG | {_g_t_p} gols | xG/chute: {_xg_shot_t_p:.3f} | Distância: {_dist_t_p:.1f}m<br>
            <b>Δ xG:</b> {_xg_t_p - _xg_b_p:+.2f} | <b>Δ Gols:</b> {_g_t_p - _g_b_p:+d} | <b>Δ Qualidade:</b> {_xg_shot_t_p - _xg_shot_b_p:+.3f} xG/chute
            {'| <span style="color:#00FF87;">✅ Posições mais perigosas no alvo</span>' if _xg_shot_t_p > _xg_shot_b_p + 0.01 else ('| <span style="color:#FF4B4B;">⚠️ Posições menos perigosas no alvo</span>' if _xg_shot_t_p < _xg_shot_b_p - 0.01 else '| ↔️ Qualidade similar entre os períodos')}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("Dados insuficientes para gerar shotmap individual comparativo.")
