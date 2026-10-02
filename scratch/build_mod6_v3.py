# -*- coding: utf-8 -*-
"""
Script to build updated app/modules/mod6_tactical_diagnosis.py
Addressing all 3 areas of user feedback.
"""

code = '''"""
Módulo 6: Diagnóstico Tático & O que Mudou?
Responde com rigor analítico e didático às perguntas fundamentais:
1. O que fez o xG subir ou descer? (Decomposição Fatorial Waterfall + Vetor Tático)
2. Se o xG aumentou, por que os gols oscilaram? Por que o time ganha ou perde mais? (Anatomia Causal dos Resultados: Ataque, Defesa, Big Chances e Goleiro)
3. O posicionamento ofensivo e a geometria de chutes mudaram? (Corredores e Zonas)
4. Quem foram os protagonistas e quais jogadores melhoraram ou pioraram? (Divergência Comparativa de Conversão, Scatter Ajustado e Deltas Coloridos)
5. Formações táticas, domínio territorial (Field Tilt) e Prancheta Tática Mplsoccer com conferência de partidas reais.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
import json
import os

def render_tactical_diagnosis_tab(df_shots: pd.DataFrame, df_matches: pd.DataFrame, df_shots_full: pd.DataFrame = None, df_matches_full: pd.DataFrame = None):
    st.markdown("### 🧠 Módulo: Diagnóstico Tático & O que Mudou?")

    st.info(
        "💡 **Eleve o Debate Tático:** Para entender o Palmeiras sob o comando de Abel Ferreira, "
        "não basta olhar números estáticos isolados. Aqui decompomos as forças matemáticas (Volume vs Qualidade), "
        "a ponte causal entre xG e gols reais, o balanço defensivo que explica vitórias e derrotas, "
        "a evolução individual dos atletas e a prancheta de esquemas táticos com conferência de jogos reais."
    )

    # Base histórica completa por padrão para garantir acesso irrestrito a 2023-2026
    m_dataset = df_matches_full if df_matches_full is not None and not df_matches_full.empty else df_matches
    s_dataset = df_shots_full if df_shots_full is not None and not df_shots_full.empty else df_shots
    pal_shots_all = s_dataset[s_dataset["is_palmeiras"] == True].copy()

    if pal_shots_all.empty or m_dataset.empty:
        st.warning("Nenhum dado disponível para análise tática.")
        return

    # =========================================================================
    # PAINEL UNIFICADO DE COMPARAÇÃO (GLOBAL PARA TODAS AS ABAS)
    # =========================================================================
    st.markdown("#### 🎯 Painel Unificado de Comparação Tática")
    st.caption("Selecione o recorte desejado abaixo. Esta escolha alimentará automaticamente **todas as abas** deste módulo.")

    all_seasons = sorted(list(m_dataset["season"].dropna().unique()), reverse=True)
    bra_m = m_dataset[m_dataset["tournament"].str.contains("Brasileir", case=False)].copy()

    c_mode, c_sel = st.columns([1.1, 2.9])
    with c_mode:
        diag_mode = st.radio(
            "Recorte de Análise:",
            ["📅 Entre Temporadas Completas", "🔄 Entre Turnos do Brasileirão", "🏆 Entre Competições"],
            key="unified_diag_mode"
        )

    with c_sel:
        if diag_mode == "📅 Entre Temporadas Completas":
            c1, c2, c3 = st.columns(3)
            with c1:
                def_base_idx = min(1, len(all_seasons) - 1)
                base_season = st.selectbox("Temporada Base (Referência):", all_seasons, index=def_base_idx, key="diag_uni_base_s")
            with c2:
                target_season = st.selectbox("Temporada Alvo (Comparação):", all_seasons, index=0, key="diag_uni_target_s")
            with c3:
                tourn_opts = ["Todas as Competições"] + sorted(list(m_dataset["tournament"].dropna().unique()))
                comp_filter = st.selectbox("Competição:", tourn_opts, key="diag_uni_tourn")

            m_base = m_dataset[m_dataset["season"] == base_season]
            m_target = m_dataset[m_dataset["season"] == target_season]
            if comp_filter != "Todas as Competições":
                m_base = m_base[m_base["tournament"] == comp_filter]
                m_target = m_target[m_target["tournament"] == comp_filter]

            label_base = f"{base_season}" + (f" ({comp_filter})" if comp_filter != "Todas as Competições" else "")
            label_target = f"{target_season}" + (f" ({comp_filter})" if comp_filter != "Todas as Competições" else "")

        elif diag_mode == "🔄 Entre Turnos do Brasileirão":
            turno_options = []
            for s_yr in sorted(list(bra_m["season"].dropna().unique()), reverse=True):
                sub = bra_m[bra_m["season"] == s_yr]
                for t in ["2º Turno", "1º Turno"]:
                    if t in sub["turno"].unique():
                        turno_options.append(f"{s_yr} - {t}")

            c1, c2 = st.columns(2)
            with c1:
                def_b_idx = turno_options.index("2026 - 1º Turno") if "2026 - 1º Turno" in turno_options else min(1, len(turno_options)-1)
                base_turno = st.selectbox("Turno Base (Referência):", turno_options, index=def_b_idx, key="diag_uni_base_t")
            with c2:
                def_t_idx = turno_options.index("2026 - 2º Turno") if "2026 - 2º Turno" in turno_options else 0
                target_turno = st.selectbox("Turno Alvo (Comparação):", turno_options, index=def_t_idx, key="diag_uni_target_t")

            b_yr, b_t = base_turno.split(" - ")
            t_yr, t_t = target_turno.split(" - ")

            m_base = bra_m[(bra_m["season"] == b_yr) & (bra_m["turno"] == b_t)]
            m_target = bra_m[(bra_m["season"] == t_yr) & (bra_m["turno"] == t_t)]
            label_base = base_turno
            label_target = target_turno

        else: # Entre Competições
            all_tourns = sorted(list(m_dataset["tournament"].dropna().unique()))
            c1, c2, c3 = st.columns(3)
            with c1:
                base_tourn = st.selectbox("Competição Base (Referência):", all_tourns, index=0, key="diag_uni_base_tr")
            with c2:
                target_tourn = st.selectbox("Competição Alvo (Comparação):", all_tourns, index=min(1, len(all_tourns)-1), key="diag_uni_target_tr")
            with c3:
                s_opt = st.selectbox("Temporada:", ["Todas as Temporadas"] + all_seasons, key="diag_uni_tr_s")

            m_base = m_dataset[m_dataset["tournament"] == base_tourn]
            m_target = m_dataset[m_dataset["tournament"] == target_tourn]
            if s_opt != "Todas as Temporadas":
                m_base = m_base[m_base["season"] == s_opt]
                m_target = m_target[m_target["season"] == s_opt]

            label_base = f"{base_tourn}" + (f" ({s_opt})" if s_opt != "Todas as Temporadas" else "")
            label_target = f"{target_tourn}" + (f" ({s_opt})" if s_opt != "Todas as Temporadas" else "")

    # Finalizações filtradas para cada período
    s_base = pal_shots_all[pal_shots_all["match_id"].isin(m_base["match_id"])].copy()
    s_target = pal_shots_all[pal_shots_all["match_id"].isin(m_target["match_id"])].copy()

    n_m_base = m_base["match_id"].nunique()
    n_m_target = m_target["match_id"].nunique()
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
        st.warning(f"⚠️ Dados insuficientes para comparar '{label_base}' ({n_m_base} jogos) e '{label_target}' ({n_m_target} jogos). Selecione outros recortes acima.")
        return

    # Cálculos matemáticos essenciais compartilhados
    v_base = n_s_base / n_m_base
    xg_total_base = s_base["xg"].sum()
    q_base = xg_total_base / n_s_base if n_s_base > 0 else 0
    xg90_base = xg_total_base / n_m_base

    v_target = n_s_target / n_m_target
    xg_total_target = s_target["xg"].sum()
    q_target = xg_total_target / n_s_target if n_s_target > 0 else 0
    xg90_target = xg_total_target / n_m_target

    delta_xg90 = xg90_target - xg90_base
    delta_v = v_target - v_base
    delta_q = q_target - q_base

    mean_q = (q_base + q_target) / 2.0
    mean_v = (v_base + v_target) / 2.0
    effect_volume = delta_v * mean_q
    effect_quality = mean_v * delta_q

    # =========================================================================
    # ABAS DO MÓDULO 6
    # =========================================================================
    t_diag1, t_diag2, t_diag3, t_diag4, t_diag5 = st.tabs([
        "🌊 1. Decomposição Fatorial (Volume vs. Qualidade)",
        "🎯 2. Por que Ganha/Perde? (Anatomia dos Gols & Defesa)",
        "📐 3. Posicionamento & Onde Chutou (Geometria)",
        "🧩 4. Protagonistas & Quem Melhorou/Piorou",
        "🛡️ 5. Formações Táticas & Prancheta Interativa"
    ])

    # -------------------------------------------------------------------------
    # ABA 1: DECOMPOSIÇÃO FATORIAL (VOLUME VS QUALIDADE)
    # -------------------------------------------------------------------------
    with t_diag1:
        st.markdown("#### 🌊 O que Fez o xG Subir ou Descer?")
        st.markdown(
            "> **🎯 A Pergunta Central:** *O Palmeiras gerou mais ou menos perigo de gol porque passou a finalizar com maior frequência (Volume) "
            "ou porque escolheu posições mais claras e desmarcadas para chutar (Qualidade)?*"
        )

        k1, k2, k3, k4 = st.columns(4)
        k1.metric(f"xG/90 (Base: {label_base})", f"{xg90_base:.2f}", f"{v_base:.1f} chutes/90 | {q_base:.3f} xG/chute")
        k2.metric(f"xG/90 (Alvo: {label_target})", f"{xg90_target:.2f}", f"{delta_xg90:+.2f} ({v_target:.1f} chutes/90)")
        k3.metric("Efeito Volume (Qtd Chutes)", f"{effect_volume:+.2f} xG/90", f"{delta_v:+.1f} chutes/90")
        k4.metric("Efeito Qualidade (Seleção)", f"{effect_quality:+.2f} xG/90", f"{delta_q:+.3f} xG/chute")

        st.markdown("---")

        c_wf, c_vec = st.columns([1.1, 1.1])

        with c_wf:
            st.markdown("##### 1. Decomposição Waterfall (Forças Matemáticas)")
            st.caption("Isola rigorosamente quanto da variação de xG/90 veio de finalizar mais vezes vs finalizar melhor.")

            fig_wf = go.Figure(go.Waterfall(
                name="Decomposição xG",
                orientation="v",
                measure=["absolute", "relative", "relative", "total"],
                x=[f"Base: {label_base}", "Efeito Volume", "Efeito Qualidade", f"Alvo: {label_target}"],
                textposition="outside",
                text=[f"{xg90_base:.2f}", f"{effect_volume:+.2f}", f"{effect_quality:+.2f}", f"{xg90_target:.2f}"],
                y=[xg90_base, effect_volume, effect_quality, xg90_target],
                connector={"line": {"color": "rgb(80, 80, 80)"}},
                decreasing={"marker": {"color": "#FF4B4B"}},
                increasing={"marker": {"color": "#00FF87"}},
                totals={"marker": {"color": "#00BFFF"}}
            ))
            fig_wf.update_layout(
                template="plotly_dark",
                height=380,
                margin=dict(l=10, r=10, t=30, b=10),
                yaxis_title="xG / 90 minutos"
            )
            st.plotly_chart(fig_wf, use_container_width=True)

        with c_vec:
            st.markdown("##### 2. Deslocamento Vetorial Tático (Volume vs Qualidade)")
            st.caption("A seta amarela indica a trajetória tática da equipe entre os dois períodos.")

            ref_v = 14.5
            ref_q = 0.100
            max_v = max(v_base, v_target) * 1.25
            max_q = max(q_base, q_target) * 1.25
            min_v = min(v_base, v_target) * 0.75
            min_q = min(q_base, q_target) * 0.75

            fig_vec = go.Figure()
            fig_vec.add_vline(x=ref_v, line_dash="dash", line_color="#555555", line_width=1.5)
            fig_vec.add_hline(y=ref_q, line_dash="dash", line_color="#555555", line_width=1.5)

            # Rótulos discretos nos cantos
            fig_vec.add_annotation(x=max(max_v, ref_v*1.2)*0.98, y=max(max_q, ref_q*1.2)*0.96, text="🔥 Ataque de Elite", showarrow=False, font=dict(color="#00FF87", size=10), xanchor="right")
            fig_vec.add_annotation(x=min_v*1.05, y=max(max_q, ref_q*1.2)*0.96, text="🎯 Clínico / Letal", showarrow=False, font=dict(color="#00BFFF", size=10), xanchor="left")
            fig_vec.add_annotation(x=max(max_v, ref_v*1.2)*0.98, y=min_q*1.05, text="🌪️ Volume Forçado", showarrow=False, font=dict(color="#FFA500", size=10), xanchor="right")
            fig_vec.add_annotation(x=min_v*1.05, y=min_q*1.05, text="⚠️ Inoperante", showarrow=False, font=dict(color="#FF4B4B", size=10), xanchor="left")

            fig_vec.add_annotation(
                x=v_target, y=q_target,
                ax=v_base, ay=q_base,
                xref="x", yref="y", axref="x", ayref="y",
                text="", showarrow=True,
                arrowhead=3, arrowsize=1.5, arrowwidth=2.5,
                arrowcolor="#FFFF00"
            )

            fig_vec.add_trace(go.Scatter(
                x=[v_base], y=[q_base],
                mode="markers+text",
                name=f"Base: {label_base}",
                marker=dict(color="#00BFFF", size=16, line=dict(color="#FFFFFF", width=2)),
                text=[f"Base ({v_base:.1f} ch, {q_base:.3f} xG)"],
                textposition="bottom center",
                hoverinfo="text",
                hovertext=[f"Base: {label_base}<br>Volume: {v_base:.1f} chutes/90<br>Qualidade: {q_base:.3f} xG/chute<br>xG/90: {xg90_base:.2f}"]
            ))
            fig_vec.add_trace(go.Scatter(
                x=[v_target], y=[q_target],
                mode="markers+text",
                name=f"Alvo: {label_target}",
                marker=dict(color="#00FF87", size=18, symbol="diamond", line=dict(color="#FFFFFF", width=2)),
                text=[f"Alvo ({v_target:.1f} ch, {q_target:.3f} xG)"],
                textposition="top center",
                hoverinfo="text",
                hovertext=[f"Alvo: {label_target}<br>Volume: {v_target:.1f} chutes/90<br>Qualidade: {q_target:.3f} xG/chute<br>xG/90: {xg90_target:.2f}"]
            ))

            fig_vec.update_layout(
                template="plotly_dark",
                height=380,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis=dict(title="Volume: Finalizações por 90 min", range=[min_v, max(max_v, ref_v*1.25)]),
                yaxis=dict(title="Qualidade Média: xG por Chute", range=[min_q, max(max_q, ref_q*1.25)]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_vec, use_container_width=True)

        st.markdown("---")

        st.markdown("##### 3. Onde a Qualidade Mudou? (Decomposição por Zona de Chute)")
        def get_zone_breakdown(df_s, n_matches, label):
            z = df_s.groupby("shot_zone").agg(
                chutes=("shot_id", "count"),
                xg_sum=("xg", "sum"),
                gols=("is_goal", "sum")
            ).reset_index()
            z["periodo"] = label
            z["chutes_por_jogo"] = (z["chutes"] / n_matches).round(2)
            z["xg_por_chute"] = (z["xg_sum"] / z["chutes"]).round(3)
            return z

        zb_base = get_zone_breakdown(s_base, n_m_base, label_base)
        zb_target = get_zone_breakdown(s_target, n_m_target, label_target)
        zb_comb = pd.concat([zb_base, zb_target], ignore_index=True)

        cz1, cz2 = st.columns([1, 1])
        with cz1:
            fig_zb_vol = px.bar(
                zb_comb, x="shot_zone", y="chutes_por_jogo", color="periodo",
                barmode="group", text="chutes_por_jogo",
                color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                template="plotly_dark",
                labels={"shot_zone": "Zona", "chutes_por_jogo": "Chutes / Jogo", "periodo": "Período"},
                title="Volume de Chutes por Jogo por Zona"
            )
            fig_zb_vol.update_layout(height=300, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig_zb_vol, use_container_width=True)

        with cz2:
            fig_zb_q = px.bar(
                zb_comb, x="shot_zone", y="xg_por_chute", color="periodo",
                barmode="group", text="xg_por_chute",
                color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                template="plotly_dark",
                labels={"shot_zone": "Zona", "xg_por_chute": "xG Médio por Chute", "periodo": "Período"},
                title="Qualidade Média (xG/Chute) por Zona"
            )
            fig_zb_q.update_layout(height=300, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig_zb_q, use_container_width=True)

    # -------------------------------------------------------------------------
    # ABA 2: ANATOMIA DOS GOLS & DEFESA (POR QUE GANHA/PERDE?)
    # -------------------------------------------------------------------------
    with t_diag2:
        st.markdown("#### 🎯 Por que o Time Vence ou Perde Mais? (Anatomia Causal dos Resultados)")
        st.markdown(
            "> **🎯 As Perguntas Fundamentais:**<br>"
            "1. *Se o xG aumentou, por que os gols reais não subiram na mesma proporção (ou caíram)?*<br>"
            "2. *Por que o time perdeu pontos mesmo produzindo xG? O que aconteceu com a defesa, com as Big Chances e com o goleiro?*",
            unsafe_allow_html=True
        )

        # Métricas completas Ofensivas e Defensivas
        gols_pro_b = m_base["palmeiras_goals"].sum()
        gols_contra_b = m_base["opponent_goals"].sum()
        xg_contra_b = m_base["opponent_xg"].sum()

        gols_pro_t = m_target["palmeiras_goals"].sum()
        gols_contra_t = m_target["opponent_goals"].sum()
        xg_contra_t = m_target["opponent_xg"].sum()

        gp_per90_b = gols_pro_b / n_m_base
        gp_per90_t = gols_pro_t / n_m_target
        gc_per90_b = gols_contra_b / n_m_base
        gc_per90_t = gols_contra_t / n_m_target

        xgc_per90_b = xg_contra_b / n_m_base
        xgc_per90_t = xg_contra_t / n_m_target

        saldo_xg_b = xg90_base - xgc_per90_b
        saldo_xg_t = xg90_target - xgc_per90_t
        saldo_gols_b = gp_per90_b - gc_per90_b
        saldo_gols_t = gp_per90_t - gc_per90_t

        eff_conv_b = (gols_pro_b / xg_total_base - 1.0) * 100 if xg_total_base > 0 else 0
        eff_conv_t = (gols_pro_t / xg_total_target - 1.0) * 100 if xg_total_target > 0 else 0

        vits_b = (m_base["result"] == "Vitória").sum()
        vits_t = (m_target["result"] == "Vitória").sum()
        derrs_b = (m_base["result"] == "Derrota").sum()
        derrs_t = (m_target["result"] == "Derrota").sum()
        aprov_b = (vits_b * 3 + (m_base["result"] == "Empate").sum()) / (n_m_base * 3) * 100
        aprov_t = (vits_t * 3 + (m_target["result"] == "Empate").sum()) / (n_m_target * 3) * 100

        # Big Chances e Goals Prevented
        bc_pro_b = m_base["big_chances_palmeiras"].mean() if "big_chances_palmeiras" in m_base.columns else 0
        bc_pro_t = m_target["big_chances_palmeiras"].mean() if "big_chances_palmeiras" in m_target.columns else 0
        bc_opp_b = m_base["big_chances_opponent"].mean() if "big_chances_opponent" in m_base.columns else 0
        bc_opp_t = m_target["big_chances_opponent"].mean() if "big_chances_opponent" in m_target.columns else 0

        gp_wev_b = m_base["palmeiras_goals_prevented"].mean() if "palmeiras_goals_prevented" in m_base.columns else 0
        gp_wev_t = m_target["palmeiras_goals_prevented"].mean() if "palmeiras_goals_prevented" in m_target.columns else 0
        gp_opp_b = m_base["opponent_goals_prevented"].mean() if "opponent_goals_prevented" in m_base.columns else 0
        gp_opp_t = m_target["opponent_goals_prevented"].mean() if "opponent_goals_prevented" in m_target.columns else 0

        # 4 Cards Chave
        c_ca1, c_ca2, c_ca3, c_ca4 = st.columns(4)
        c_ca1.metric(
            "Gols Marcados / Jogo",
            f"{gp_per90_t:.2f}",
            f"{gp_per90_t - gp_per90_b:+.2f} vs Base ({gp_per90_b:.2f})"
        )
        c_ca2.metric(
            "Eficiência Ofensiva (G vs xG)",
            f"{eff_conv_t:+.1f}%",
            f"{eff_conv_t - eff_conv_b:+.1f}% vs Base ({eff_conv_b:+.1f}%)"
        )
        c_ca3.metric(
            "xG Sofrido / Jogo (Defesa)",
            f"{xgc_per90_t:.2f}",
            f"{xgc_per90_t - xgc_per90_b:+.2f} vs Base ({xgc_per90_b:.2f})",
            delta_color="inverse"
        )
        c_ca4.metric(
            "Aproveitamento de Pontos",
            f"{aprov_t:.1f}%",
            f"{aprov_t - aprov_b:+.1f}% vs Base ({aprov_b:.1f}%)"
        )

        st.markdown("---")

        # Visualização Integrada de xG e Gols Ofensivos e Defensivos
        st.markdown("##### 1. Comparação Visual Integrada: xG e Gols Ofensivos vs. Defensivos")
        st.caption("Veja lado a lado a produção do ataque e a solidez da defesa nos dois períodos.")

        c_v1, c_v2 = st.columns([1, 1])

        with c_v1:
            st.markdown("###### ⚔️ Produção Ofensiva (xG Pró vs. Gols Marcados)")
            st.caption("Mede se o ataque gerou chances e se as converteu na rede.")

            df_of = pd.DataFrame({
                "Métrica": ["xG Pró / 90 min (Criação)", "Gols Pró / 90 min (Rede)"],
                label_base: [round(xg90_base, 2), round(gp_per90_b, 2)],
                label_target: [round(xg90_target, 2), round(gp_per90_t, 2)]
            })
            df_of_m = pd.melt(df_of, id_vars=["Métrica"], var_name="Período", value_name="Média/Jogo")

            fig_of = px.bar(
                df_of_m, x="Métrica", y="Média/Jogo", color="Período",
                barmode="group", text="Média/Jogo",
                color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                template="plotly_dark"
            )
            fig_of.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_of, use_container_width=True)

        with c_v2:
            st.markdown("###### 🛡️ Solidez Defensiva (xG Concedido vs. Gols Sofridos)")
            st.caption("Mede a exposição da zaga e quantos gols o rival efetivamente marcou.")

            df_def = pd.DataFrame({
                "Métrica": ["xG Sofrido / 90 min (Perigo)", "Gols Sofridos / 90 min (Rede)"],
                label_base: [round(xgc_per90_b, 2), round(gc_per90_b, 2)],
                label_target: [round(xgc_per90_t, 2), round(gc_per90_t, 2)]
            })
            df_def_m = pd.melt(df_def, id_vars=["Métrica"], var_name="Período", value_name="Média/Jogo")

            fig_def = px.bar(
                df_def_m, x="Métrica", y="Média/Jogo", color="Período",
                barmode="group", text="Média/Jogo",
                color_discrete_map={label_base: "#00BFFF", label_target: "#FF4B4B"},
                template="plotly_dark"
            )
            fig_def.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_def, use_container_width=True)

        st.markdown("---")

        # Informações Relevantes Adicionais: Big Chances & Goleiros
        st.markdown("##### 2. O que Mais Explica os Resultados? Grandes Chances & Desempenho de Goleiros")
        st.caption("Variáveis ocultas que explicam oscilações de placar independentemente da posse de bola.")

        c_inf1, c_inf2, c_inf3 = st.columns(3)

        with c_inf1:
            st.markdown("###### ⭐ Grandes Chances (Big Chances / Jogo)")
            st.caption("Chances claríssimas de gol (cara a cara ou pequena área).")
            fig_bc = go.Figure()
            fig_bc.add_trace(go.Bar(
                x=[label_base, label_target], y=[round(bc_pro_b, 2), round(bc_pro_t, 2)],
                name="Big Chances Criadas", marker_color="#00FF87",
                text=[f"{bc_pro_b:.2f}", f"{bc_pro_t:.2f}"], textposition="outside"
            ))
            fig_bc.add_trace(go.Bar(
                x=[label_base, label_target], y=[round(bc_opp_b, 2), round(bc_opp_t, 2)],
                name="Big Chances Sofridas", marker_color="#FF4B4B",
                text=[f"{bc_opp_b:.2f}", f"{bc_opp_t:.2f}"], textposition="outside"
            ))
            fig_bc.update_layout(
                template="plotly_dark", height=280, barmode="group",
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_bc, use_container_width=True)

        with c_inf2:
            st.markdown("###### 🧤 Gols Evitados pelo Goleiro (Goals Prevented)")
            st.caption("Post-Shot xG defendido. Positivo = goleiro operou milagres.")
            fig_gp = go.Figure()
            fig_gp.add_trace(go.Bar(
                x=[label_base, label_target], y=[round(gp_wev_b, 2), round(gp_wev_t, 2)],
                name="Weverton (Salvos / Jogo)", marker_color="#00BFFF",
                text=[f"{gp_wev_b:+.2f}", f"{gp_wev_t:+.2f}"], textposition="outside"
            ))
            fig_gp.add_trace(go.Bar(
                x=[label_base, label_target], y=[round(gp_opp_b, 2), round(gp_opp_t, 2)],
                name="Goleiros Rivais (Salvos / Jogo)", marker_color="#FFA500",
                text=[f"{gp_opp_b:+.2f}", f"{gp_opp_t:+.2f}"], textposition="outside"
            ))
            fig_gp.update_layout(
                template="plotly_dark", height=280, barmode="group",
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_gp, use_container_width=True)

        with c_inf3:
            st.markdown("###### ⚖️ Saldo Real de Gols vs. Saldo xG")
            st.caption("Descolamento entre placar real e justiça estatística.")
            fig_s = go.Figure()
            fig_s.add_trace(go.Bar(
                x=[label_base, label_target], y=[round(saldo_gols_b, 2), round(saldo_gols_t, 2)],
                name="Saldo Real (Gols/J)", marker_color="#00FF87",
                text=[f"{saldo_gols_b:+.2f}", f"{saldo_gols_t:+.2f}"], textposition="outside"
            ))
            fig_s.add_trace(go.Bar(
                x=[label_base, label_target], y=[round(saldo_xg_b, 2), round(saldo_xg_t, 2)],
                name="Saldo Esperado (xG/J)", marker_color="#00BFFF",
                text=[f"{saldo_xg_b:+.2f}", f"{saldo_xg_t:+.2f}"], textposition="outside"
            ))
            fig_s.update_layout(
                template="plotly_dark", height=280, barmode="group",
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_s, use_container_width=True)

        st.markdown("---")

        # Diagnóstico Causal Detalhado
        st.markdown("##### 3. Diagnóstico Causal Explicativo")

        if eff_conv_b > 25 and eff_conv_t < eff_conv_b:
            conv_text = (
                f"No período base (**{label_base}**), o Palmeiras operava em uma letalidade atípica e insustentável "
                f"(marcou **{eff_conv_b:+.1f}%** de gols acima do xG esperado). No período alvo (**{label_target}**), "
                f"a pontaria regrediu para um patamar mais próximo da média histórica ({eff_conv_t:+.1f}%). "
                f"Por isso, mesmo criando mais xG ({xg90_target:.2f} vs {xg90_base:.2f}), os gols não subiram no mesmo ritmo."
            )
        elif eff_conv_t > eff_conv_b:
            conv_text = (
                f"O Palmeiras aumentou sua eficiência de finalização de **{eff_conv_b:+.1f}%** para **{eff_conv_t:+.1f}%** acima do xG, "
                f"indicando fase inspirada dos seus atacantes e finalizações mais letais que desafiaram a média probabilística."
            )
        else:
            conv_text = (
                f"A taxa de conversão ofensiva permaneceu estável entre os períodos ({eff_conv_b:+.1f}% vs {eff_conv_t:+.1f}%), "
                f"de modo que a produção de gols refletiu fielmente a geração estrutural de chances."
            )

        delta_def = xgc_per90_t - xgc_per90_b
        if delta_def > 0.20:
            def_text = (
                f"A defesa ficou significativamente **mais exposta**: concedeu **{xgc_per90_t:.2f} xG sofrido por jogo** "
                f"no alvo contra **{xgc_per90_b:.2f}** na base ({delta_def:+.2f} xG/jogo a mais para o adversário). "
                f"As Big Chances cedidas subiram de {bc_opp_b:.2f} para {bc_opp_t:.2f} por jogo. "
                f"Essa maior concessão de chances claras no campo de defesa explica por que o aproveitamento caiu de {aprov_b:.1f}% para {aprov_t:.1f}%."
            )
        elif delta_def < -0.15:
            def_text = (
                f"A defesa apresentou **evolução estrutural**, reduzindo as chances concedidas de **{xgc_per90_b:.2f}** para **{xgc_per90_t:.2f} xG sofrido/jogo**, "
                f"garantindo maior proteção à meta de Weverton e sustentando o aproveitamento de pontos ({aprov_t:.1f}%)."
            )
        else:
            def_text = (
                f"O nível de perigo concedido pela defesa manteve-se equilibrado ({xgc_per90_b:.2f} vs {xgc_per90_t:.2f} xG sofrido/jogo). "
                f"As oscilações no placar foram fruto de margens finas e variância natural em partidas de um gol de diferença."
            )

        st.info(f"💡 **Por que os Gols Oscilaram?** {conv_text}")
        st.warning(f"🛡️ **Por que o Aproveitamento Mudou?** {def_text}")

    # -------------------------------------------------------------------------
    # ABA 3: POSICIONAMENTO E GEOMETRIA
    # -------------------------------------------------------------------------
    with t_diag3:
        st.markdown("#### 📐 O Posicionamento e a Geometria de Chute Mudaram?")
        st.markdown(
            "> **🎯 A Pergunta Central:** *O Palmeiras afunilou mais o jogo pelo centro ou abriu o jogo pelas pontas? "
            "E a que distância do gol o time tem concluído as jogadas?*"
        )

        dist_base = s_base["distance_meters"].mean()
        dist_target = s_target["distance_meters"].mean()
        ang_base = s_base["angle_degrees"].mean()
        ang_target = s_target["angle_degrees"].mean()
        in_box_base = (s_base["shot_zone"] != "Fora da Área").mean() * 100
        in_box_target = (s_target["shot_zone"] != "Fora da Área").mean() * 100

        cg1, cg2, cg3 = st.columns(3)
        cg1.metric("Distância Média do Gol", f"{dist_target:.1f} m", f"{dist_target - dist_base:+.1f} m vs Base ({dist_base:.1f} m)", delta_color="inverse")
        cg2.metric("Ângulo Médio de Visão", f"{ang_target:.1f}°", f"{ang_target - ang_base:+.1f}° vs Base ({ang_base:.1f}°)")
        cg3.metric("% Chutes Dentro da Área", f"{in_box_target:.1f}%", f"{in_box_target - in_box_base:+.1f}% vs Base ({in_box_base:.1f}%)")

        st.markdown("---")

        cp1, cp2 = st.columns([1, 1])

        with cp1:
            st.markdown("##### 1. Ocupação dos Corredores (Esquerdo / Centro / Direito)")
            def get_corr_df(df_s, label):
                c = df_s.groupby("shot_corridor").agg(chutes=("shot_id", "count")).reset_index()
                c["pct"] = (c["chutes"] / c["chutes"].sum() * 100).round(1)
                c["periodo"] = label
                return c

            c_comb = pd.concat([get_corr_df(s_base, label_base), get_corr_df(s_target, label_target)], ignore_index=True)

            fig_corr = px.bar(
                c_comb, x="shot_corridor", y="pct", color="periodo",
                barmode="group", text=c_comb["pct"].apply(lambda p: f"{p}%"),
                color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                template="plotly_dark",
                labels={"shot_corridor": "Corredor", "pct": "% das Finalizações", "periodo": "Período"}
            )
            fig_corr.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_corr, use_container_width=True)

        with cp2:
            st.markdown("##### 2. Distribuição por Zona da Finalização")
            def get_zp_df(df_s, label):
                z = df_s.groupby("shot_zone").agg(chutes=("shot_id", "count")).reset_index()
                z["pct"] = (z["chutes"] / z["chutes"].sum() * 100).round(1)
                z["periodo"] = label
                return z

            z_comb = pd.concat([get_zp_df(s_base, label_base), get_zp_df(s_target, label_target)], ignore_index=True)

            fig_zp = px.bar(
                z_comb, x="shot_zone", y="pct", color="periodo",
                barmode="group", text=z_comb["pct"].apply(lambda p: f"{p}%"),
                color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                template="plotly_dark",
                labels={"shot_zone": "Zona", "pct": "% das Finalizações", "periodo": "Período"}
            )
            fig_zp.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_zp, use_container_width=True)

    # -------------------------------------------------------------------------
    # ABA 4: PROTAGONISTAS & QUEM MELHOROU/PIOROU
    # -------------------------------------------------------------------------
    with t_diag4:
        st.markdown("#### 🧩 Protagonistas Ofensivos & Quem Melhorou ou Piorou?")
        st.markdown(
            "> **🎯 As Perguntas Centrais:** *Quais atacantes foram letais e quais desperdiçaram chances criadas? "
            "E no comparativo direto entre os dois períodos, quem ganhou espaço e quem perdeu rendimento?*"
        )

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

        # Destaques em Cards com Filtro Mínimo de Gols e Volume para evitar ruído
        top_players = pm[pm["chutes_total"] >= 3].sort_values(by="xg_total_ambos", ascending=False).copy()

        if not top_players.empty:
            most_growth_xg = pm.sort_values(by="delta_xg", ascending=False).iloc[0]
            most_drop_xg = pm.sort_values(by="delta_xg", ascending=True).iloc[0]

            # Filtro mínimo de relevância em gols: atletas com ao menos 2 gols no total
            scorers = pm[pm["gols_total"] >= 2].sort_values(by="delta_gols", ascending=False)
            if not scorers.empty:
                most_growth_gols = scorers.iloc[0]
            else:
                most_growth_gols = pm.sort_values(by="delta_gols", ascending=False).iloc[0]

            cd1, cd2, cd3 = st.columns(3)
            cd1.metric(
                "🚀 Maior Ganho de Criação (xG)",
                most_growth_xg["player_name"],
                f"{most_growth_xg['delta_xg']:+.2f} xG ({most_growth_xg['xg_b']:.2f} ➔ {most_growth_xg['xg_t']:.2f})"
            )
            cd2.metric(
                "🎯 Maior Salto em Gols (Min. 2 Gols)",
                most_growth_gols["player_name"],
                f"{most_growth_gols['delta_gols']:+d} gols ({int(most_growth_gols['gols_b'])} ➔ {int(most_growth_gols['gols_t'])})"
            )
            cd3.metric(
                "📉 Maior Queda de Produção",
                most_drop_xg["player_name"],
                f"{most_drop_xg['delta_xg']:+.2f} xG ({most_drop_xg['xg_b']:.2f} ➔ {most_drop_xg['xg_t']:.2f})",
                delta_color="inverse"
            )

        st.markdown("---")

        c_eff, c_scat = st.columns([1.1, 1.1])

        with c_eff:
            st.markdown("##### 1. Divergência de Conversão Comparativa (Base vs. Alvo)")
            st.caption("Saldo de Gols marcados menos xG esperado (G - xG). Compara a letalidade de cada atacante nos dois períodos.")

            # Pegar top 8 atletas de maior xG somado para comparar Base e Alvo
            eff_candidates = top_players.head(8).copy()
            if not eff_candidates.empty:
                eff_melt = pd.DataFrame({
                    "Atleta": list(eff_candidates["player_name"]) + list(eff_candidates["player_name"]),
                    "Saldo Letalidade (G - xG)": list(eff_candidates["diff_eff_b"]) + list(eff_candidates["diff_eff_t"]),
                    "Período": [label_base] * len(eff_candidates) + [label_target] * len(eff_candidates)
                })

                fig_diverg = px.bar(
                    eff_melt, x="Saldo Letalidade (G - xG)", y="Atleta", color="Período",
                    barmode="group", orientation="h", text="Saldo Letalidade (G - xG)",
                    color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                    template="plotly_dark"
                )
                fig_diverg.add_vline(x=0, line_color="#888888", line_width=1.5)
                fig_diverg.update_layout(
                    height=380, margin=dict(l=10, r=10, t=30, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                    yaxis=dict(categoryorder="total ascending")
                )
                st.plotly_chart(fig_diverg, use_container_width=True)
            else:
                st.info("Amostra insuficiente para o gráfico comparativo de divergência.")

        with c_scat:
            st.markdown("##### 2. Mapa de Eficiência dos Finalizadores (Scatter xG vs Gols)")
            st.caption("Eixos ajustados estritamente à amplitude real dos dados. Linha diagonal = paridade esperada.")

            scat_list = []
            for _, r in top_players.iterrows():
                if r["chutes_b"] >= 2:
                    scat_list.append({"Atleta": r["player_name"], "xG": r["xg_b"], "Gols": r["gols_b"], "Chutes": r["chutes_b"], "Período": label_base})
                if r["chutes_t"] >= 2:
                    scat_list.append({"Atleta": r["player_name"], "xG": r["xg_t"], "Gols": r["gols_t"], "Chutes": r["chutes_t"], "Período": label_target})
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
                    color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
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

        # Tabela Colorida de Deltas
        st.markdown("##### 3. Balanço Completo da Evolução dos Jogadores (Deltas)")
        st.caption("Verde = evolução positiva; Vermelho = queda de produção. Ordenado por volume somado de chances.")

        disp_df = top_players[[
            "player_name", "xg_b", "xg_t", "delta_xg", "gols_b", "gols_t", "delta_gols", "diff_eff_b", "diff_eff_t"
        ]].copy()

        disp_df = disp_df.rename(columns={
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

        # Função de estilização com cores suaves
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
        }).applymap(style_deltas, subset=["Δ xG", "Δ Gols", f"Letalidade ({label_base})", f"Letalidade ({label_target})"])

        st.dataframe(styled_table, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # ABA 5: FORMAÇÕES TÁTICAS, FIELD TILT & PRANCHETA INTERATIVA
    # -------------------------------------------------------------------------
    with t_diag5:
        st.markdown("#### 🛡️ Formações Táticas, Domínio Territorial & Prancheta Interativa")

        # Banner Front-and-Center de Field Tilt
        st.markdown(
            """
            <div style="background-color: #1A2332; border: 1px solid #2A3B50; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;">
                <h4 style="color: #00FF87; margin-top: 0; margin-bottom: 8px;">📖 O que é Field Tilt (% de Domínio Territorial)?</h4>
                <p style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.5; margin-bottom: 10px;">
                    O <b>Field Tilt</b> mede a porcentagem de ações no <b>terço ofensivo</b> do campo em relação ao rival:
                </p>
                <div style="background-color: #0F172A; padding: 8px; border-radius: 6px; text-align: center; font-family: monospace; color: #38BDF8; font-size: 0.98rem; margin-bottom: 10px;">
                    Field Tilt (%) = [ Ações no Terço Ofensivo (Palmeiras) ÷ Ações Totais no Terço Ofensivo (Ambos) ] × 100
                </div>
                <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 220px; background: rgba(0,255,135,0.08); padding: 8px 12px; border-radius: 6px; border-left: 3px solid #00FF87; font-size: 0.88rem; color: #CBD5E1;">
                        <b>Supera a Posse Comum:</b> A posse tradicional conta toques lentos entre zagueiros na própria defesa. O Field Tilt revela quem realmente encurrala o adversário.
                    </div>
                    <div style="flex: 1; min-width: 220px; background: rgba(0,191,255,0.08); padding: 8px 12px; border-radius: 6px; border-left: 3px solid #00BFFF; font-size: 0.88rem; color: #CBD5E1;">
                        <b>Escala:</b> <b>&gt;60%:</b> Domínio sufocante | <b>50%–60%:</b> Controle territorial positivo | <b>&lt;50%:</b> Jogo reativo
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            "> **🎯 O Enigma de Abel Ferreira:** *Como cada formação molda a balança entre criar perigo (xG e Gols Pró) "
            "e conceder contra-ataques (xG e Gols Sofridos)?*",
            unsafe_allow_html=True
        )

        if "palmeiras_formation" not in m_dataset.columns or "field_tilt" not in m_dataset.columns:
            st.warning("⚠️ Dados estruturais de formação e Field Tilt ainda não estão carregados.")
            return

        # Análise direta sobre o dataset sem filtros adicionais de temporada
        form_df = m_dataset[
            (m_dataset["palmeiras_formation"].notna()) & 
            (m_dataset["palmeiras_formation"] != "Desconhecida")
        ].copy()

        form_df["familia_tatica"] = form_df["palmeiras_formation"].apply(
            lambda f: "Linha de 3/5 Zagueiros" if str(f).startswith(("3-", "5-")) else "Linha de 4 Defensores"
        )

        # Formações mais frequentes (mínimo 3 partidas)
        form_counts = form_df["palmeiras_formation"].value_counts()
        valid_formations = form_counts[form_counts >= 3].index.tolist()
        form_filtered = form_df[form_df["palmeiras_formation"].isin(valid_formations)].copy()

        f_agg = form_filtered.groupby("palmeiras_formation").agg(
            partidas=("match_id", "count"),
            vitorias=("result", lambda s: (s == "Vitória").sum()),
            aproveitamento=("result", lambda s: ((s == "Vitória").sum() * 3 + (s == "Empate").sum()) / (len(s) * 3) * 100),
            xg_pro=("palmeiras_xg", "mean"),
            xg_contra=("opponent_xg", "mean"),
            gols_pro=("palmeiras_goals", "mean"),
            gols_contra=("opponent_goals", "mean"),
            field_tilt=("field_tilt", "mean"),
            toques_area=("palmeiras_touches_in_box", "mean"),
            cruzamentos=("palmeiras_crosses_attempted", "mean"),
            through_balls=("palmeiras_through_balls", "mean"),
            posse=("palmeiras_possession", "mean")
        ).reset_index()

        f_agg["saldo_xg"] = (f_agg["xg_pro"] - f_agg["xg_contra"]).round(2)
        f_agg["saldo_gols"] = (f_agg["gols_pro"] - f_agg["gols_contra"]).round(2)
        f_agg["xg_pro"] = f_agg["xg_pro"].round(2)
        f_agg["xg_contra"] = f_agg["xg_contra"].round(2)
        f_agg["gols_pro"] = f_agg["gols_pro"].round(2)
        f_agg["gols_contra"] = f_agg["gols_contra"].round(2)
        f_agg["field_tilt"] = f_agg["field_tilt"].round(1)
        f_agg["toques_area"] = f_agg["toques_area"].round(1)
        f_agg["cruzamentos"] = f_agg["cruzamentos"].round(1)
        f_agg["through_balls"] = f_agg["through_balls"].round(2)
        f_agg["posse"] = f_agg["posse"].round(1)
        f_agg["aproveitamento"] = f_agg["aproveitamento"].round(1)

        # 1. Cards de Perfil Tático Destacado
        best_def = f_agg.sort_values(by="xg_contra", ascending=True).iloc[0]
        best_att = f_agg.sort_values(by="xg_pro", ascending=False).iloc[0]
        best_tilt = f_agg.sort_values(by="field_tilt", ascending=False).iloc[0]
        best_balance = f_agg.sort_values(by="saldo_xg", ascending=False).iloc[0]

        st.markdown("##### 1. Perfis Táticos: Qual Formação Entrega Cada Vantagem?")
        st.caption("Baseado em todo o histórico estrutural do Palmeiras com Abel Ferreira.")

        c_p1, c_p2, c_p3, c_p4 = st.columns(4)
        c_p1.metric("🛡️ Melhor Defesa", best_def["palmeiras_formation"], f"{best_def['xg_contra']:.2f} xG sofrido/j ({best_def['partidas']} jogos)")
        c_p2.metric("⚔️ Melhor Ataque", best_att["palmeiras_formation"], f"{best_att['xg_pro']:.2f} xG pró/j ({best_att['partidas']} jogos)")
        c_p3.metric("🏟️ Maior Domínio Territorial", best_tilt["palmeiras_formation"], f"{best_tilt['field_tilt']:.1f}% Field Tilt ({best_tilt['partidas']} jogos)")
        c_p4.metric("⚖️ Maior Saldo Estrutural", best_balance["palmeiras_formation"], f"{best_balance['saldo_xg']:+.2f} Saldo xG/j ({best_balance['partidas']} jogos)")

        st.markdown("---")

        # 2. Gráficos Comparativos de Ataque e Defesa por Formação
        st.markdown("##### 2. O Impacto Real de Cada Esquema: xG e Gols Pró vs. Contra")
        st.caption("Compara a capacidade de criar e a vulnerabilidade defensiva em cada desenho tático.")

        c_fg1, c_fg2 = st.columns([1, 1])

        with c_fg1:
            st.markdown("###### Saldo de xG Esperado (xG Pró vs. xG Contra)")
            fig_fx = go.Figure()
            fig_fx.add_trace(go.Bar(
                x=f_agg["palmeiras_formation"], y=f_agg["xg_pro"],
                name="xG Pró / Jogo", marker_color="#00FF87",
                text=f_agg["xg_pro"], textposition="outside"
            ))
            fig_fx.add_trace(go.Bar(
                x=f_agg["palmeiras_formation"], y=f_agg["xg_contra"],
                name="xG Sofrido / Jogo", marker_color="#FF4B4B",
                text=f_agg["xg_contra"], textposition="outside"
            ))
            fig_fx.update_layout(
                template="plotly_dark", height=330, barmode="group",
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_fx, use_container_width=True)

        with c_fg2:
            st.markdown("###### Saldo de Gols Reais (Gols Marcados vs. Sofridos)")
            fig_fg = go.Figure()
            fig_fg.add_trace(go.Bar(
                x=f_agg["palmeiras_formation"], y=f_agg["gols_pro"],
                name="Gols Marcados / Jogo", marker_color="#00BFFF",
                text=f_agg["gols_pro"], textposition="outside"
            ))
            fig_fg.add_trace(go.Bar(
                x=f_agg["palmeiras_formation"], y=f_agg["gols_contra"],
                name="Gols Sofridos / Jogo", marker_color="#FFA500",
                text=f_agg["gols_contra"], textposition="outside"
            ))
            fig_fg.update_layout(
                template="plotly_dark", height=330, barmode="group",
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_fg, use_container_width=True)

        # Tabela Completa Formatada
        st.markdown("##### 3. Tabela Comparativa Completa por Esquema Tático")
        disp_form = f_agg.rename(columns={
            "palmeiras_formation": "Formação",
            "partidas": "Jogos",
            "aproveitamento": "Aprov. (%)",
            "xg_pro": "xG Pró/J",
            "xg_contra": "xG Contra/J",
            "saldo_xg": "Saldo xG",
            "gols_pro": "Gols Pró/J",
            "gols_contra": "Gols Contra/J",
            "saldo_gols": "Saldo Gols",
            "field_tilt": "Field Tilt (%)",
            "toques_area": "Toques Área/J",
            "cruzamentos": "Cruzamentos/J",
            "through_balls": "Passes Prof./J",
            "posse": "Posse (%)"
        })
        st.dataframe(disp_form.sort_values(by="Jogos", ascending=False), use_container_width=True, hide_index=True)

        st.markdown("---")

        # ---------------------------------------------------------------------
        # 4. PRANCHETA TÁTICA COM MPLSOCCER & VERIFICADOR DE JOGOS REAIS
        # ---------------------------------------------------------------------
        st.markdown("##### 🏟️ 4. Prancheta Tática & Verificador de Escalações em Campo")
        st.markdown(
            "> *\"Nem sempre o SofaScore detecta corretamente qual a formação em campo e gostaria de conferir.\"*<br>"
            "Aqui você pode visualizar a prancheta de posicionamento em alta fidelidade e inspecionar **os 11 titulares escalados em qualquer partida real**.",
            unsafe_allow_html=True
        )

        def draw_mpl_pitch(formation_str, players=None):
            pitch = VerticalPitch(
                pitch_type="custom",
                pitch_length=105,
                pitch_width=68,
                half=False,
                pitch_color="#122416",
                line_color="#4A7552",
                linewidth=2,
                goal_type="box"
            )
            fig, ax = pitch.draw(figsize=(6.5, 8.5))
            fig.patch.set_facecolor("#0F172A")

            try:
                lines = [int(x) for x in str(formation_str).split('-')]
            except:
                lines = [4, 4, 2]

            coords = [(8, 34)]
            n_lines = len(lines)
            x_positions = [24 + i * (68 / max(1, n_lines - 1)) for i in range(n_lines)]

            for idx, (count, x_val) in enumerate(zip(lines, x_positions)):
                if count == 1:
                    ys = [34]
                elif count == 2:
                    ys = [24, 44]
                elif count == 3:
                    ys = [18, 34, 50] if idx == 0 else [12, 34, 56]
                elif count == 4:
                    ys = [10, 26, 42, 58]
                elif count == 5:
                    ys = [8, 21, 34, 47, 60]
                else:
                    ys = [10 + j * (48 / (count - 1)) for j in range(count)]
                for y_val in ys:
                    coords.append((x_val, y_val))

            xs = [c[0] for c in coords[:11]]
            ys = [c[1] for c in coords[:11]]

            pitch.scatter(xs, ys, s=460, color="#00FF87", edgecolors="#FFFFFF", linewidth=2.5, zorder=3, ax=ax)

            for i, (x, y) in enumerate(zip(xs, ys)):
                if players and i < len(players):
                    p = players[i]
                    shirt = str(p.get("shirtNumber", ""))
                    name = p.get("name", "").split()[-1]
                    ax.text(y, x, shirt, color="#0A1E11", fontsize=9.5, fontweight="bold", ha="center", va="center", zorder=4)
                    ax.text(y, x - 4.5, name, color="#FFFFFF", fontsize=8.5, fontweight="bold", ha="center", va="top", zorder=4,
                            bbox=dict(boxstyle="round,pad=0.2", facecolor="#1E293B", edgecolor="none", alpha=0.85))
                else:
                    role_labels = ["GOL", "LAT/ZAG", "ZAG", "ZAG", "LAT/ZAG", "VOL", "VOL", "MEI", "MEI", "MEI", "ATA"]
                    lbl = role_labels[i] if i < len(role_labels) else "JOG"
                    ax.text(y, x - 4.5, lbl, color="#FFFFFF", fontsize=8, fontweight="bold", ha="center", va="top", zorder=4,
                            bbox=dict(boxstyle="round,pad=0.2", facecolor="#1E293B", edgecolor="none", alpha=0.85))

            plt.tight_layout()
            return fig

        all_valid_forms = valid_formations if not form_filtered.empty else ["4-2-3-1", "3-4-2-1", "3-5-2", "4-4-2", "4-3-3"]

        c_pf1, c_pf2 = st.columns([1.1, 1.9])
        with c_pf1:
            sel_form = st.selectbox("Selecione a Formação Tática:", all_valid_forms, key="board_sel_form_v3")
            board_mode = st.radio(
                "Modo de Exibição:",
                ["📐 Gabarito Tático Teórico", "🔍 Conferir Jogo Real no Campo"],
                key="board_mode_radio_v3"
            )

            real_players = None
            match_info = None

            if board_mode == "🔍 Conferir Jogo Real no Campo":
                matches_with_form = form_df[form_df["palmeiras_formation"] == sel_form].sort_values(by="date", ascending=False)
                if not matches_with_form.empty:
                    match_opts = {}
                    for _, r in matches_with_form.iterrows():
                        key_str = f"{r['date']} - {r['tournament']}: {r['home_team']} {r['home_score']}x{r['away_score']} {r['away_team']} ({r['result']})"
                        match_opts[key_str] = r

                    chosen_match_label = st.selectbox(
                        f"Escolha a partida ({len(match_opts)} jogos):",
                        list(match_opts.keys()),
                        key="board_match_picker_v3"
                    )
                    chosen_row = match_opts[chosen_match_label]
                    match_info = chosen_row

                    json_path = f"data/raw/{chosen_row['season']}/event_{chosen_row['match_id']}_lineups.json"
                    if os.path.exists(json_path):
                        with open(json_path, encoding="utf-8") as f_json:
                            d_lineup = json.load(f_json)
                        side = "home" if chosen_row["is_palmeiras_home"] else "away"
                        if side in d_lineup and "players" in d_lineup[side]:
                            starters = [p for p in d_lineup[side]["players"] if not p.get("substitute")]
                            real_players = []
                            for p in starters:
                                real_players.append({
                                    "name": p.get("player", {}).get("name", "Jogador"),
                                    "shirtNumber": p.get("shirtNumber", ""),
                                    "position": p.get("position", "")
                                })

            if match_info is not None:
                st.markdown(
                    f"**Conferência da Partida:**<br>"
                    f"🏆 **{match_info['tournament']}** | 📅 {match_info['date']}<br>"
                    f"⚽ Placar: **{match_info['palmeiras_score']} x {match_info['opponent_score']}** vs {match_info['opponent_name']}<br>"
                    f"📊 Posse: {match_info['palmeiras_possession']:.1f}% | Field Tilt: {match_info['field_tilt']:.1f}%",
                    unsafe_allow_html=True
                )
                if real_players:
                    st.caption("Titulares: " + ", ".join([f"{p['name']} (#{p['shirtNumber']})" for p in real_players]))

        with c_pf2:
            fig_pitch = draw_mpl_pitch(sel_form, real_players)
            st.pyplot(fig_pitch, use_container_width=True)
            plt.close(fig_pitch)

    # =========================================================================
    # GUIA METODOLÓGICO EXPANDÍVEL NO RODAPÉ
    # =========================================================================
    with st.expander("📖 Guia Metodológico & Formulações Matemáticas (Consulta Aprofundada)", expanded=False):
        st.markdown(r"""
        ### 🎯 Qual pergunta cada análise responde?
        1. **Decomposição Fatorial Waterfall:** Separa rigorosamente o efeito de volume do efeito de qualidade posicional.
           $$\\Delta xG_{90} = \\Delta V \\cdot \\bar{Q} + \\bar{V} \\cdot \\Delta Q$$
        2. **Anatomia Causal dos Resultados:** Separa o efeito de criação ($xG$) da letalidade ($Gols/xG$) e investiga o balanço defensivo ($xG$ sofrido, Big Chances e Gols Evitados) para explicar por que o time venceu ou perdeu mais jogos.
        3. **Vetor de Deslocamento Tático:** Posiciona a equipe em 4 quadrantes ofensivos e traça a rota de evolução.
        4. **Field Tilt (%):** Proporção de ações no terço ofensivo em relação ao adversário. Revela dominância territorial verdadeira.
        5. **Prancheta Tática & Verificador de Escalações:** Permite ao usuário conferir a fidedignidade da detecção do SofaScore inspecionando os 11 titulares em qualquer partida da história recente.
        """)
'''

with open("app/modules/mod6_tactical_diagnosis.py", "w", encoding="utf-8") as f:
    f.write(code)

print("mod6_tactical_diagnosis.py updated to v3 successfully!")
