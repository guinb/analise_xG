# -*- coding: utf-8 -*-
"""
Full refactor script for app/modules/mod6_tactical_diagnosis.py
"""

code = '''"""
Módulo 6: Diagnóstico Tático & O que Mudou?
Responde com rigor analítico e didático às perguntas fundamentais:
1. O que fez o xG subir ou descer? (Decomposição Fatorial Waterfall + Vetor Tático)
2. Se o xG aumentou, por que os gols oscilaram? Por que o time ganha ou perde mais? (Anatomia Causal dos Resultados)
3. O posicionamento ofensivo e a geometria de chutes mudaram? (Corredores e Zonas)
4. Quem foram os protagonistas e quais jogadores melhoraram ou pioraram? (Divergência de Conversão e Deltas)
5. Formações táticas, domínio territorial (Field Tilt) e Prancheta Tática Interativa com conferência de partidas reais.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
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

        # Cards limpos e descomplicados
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

            ref_v = 14.5  # Média de chutes típica
            ref_q = 0.100 # xG médio por chute típico
            max_v = max(v_base, v_target) * 1.25
            max_q = max(q_base, q_target) * 1.25
            min_v = min(v_base, v_target) * 0.75
            min_q = min(q_base, q_target) * 0.75

            fig_vec = go.Figure()

            # Linhas de referência dos quadrantes
            fig_vec.add_vline(x=ref_v, line_dash="dash", line_color="#555555", line_width=1.5)
            fig_vec.add_hline(y=ref_q, line_dash="dash", line_color="#555555", line_width=1.5)

            # Rótulos discretos nos 4 cantos externos para não poluir o centro
            fig_vec.add_annotation(x=max(max_v, ref_v*1.2)*0.98, y=max(max_q, ref_q*1.2)*0.96, text="🔥 Ataque de Elite", showarrow=False, font=dict(color="#00FF87", size=10), xanchor="right")
            fig_vec.add_annotation(x=min_v*1.05, y=max(max_q, ref_q*1.2)*0.96, text="🎯 Clínico / Letal", showarrow=False, font=dict(color="#00BFFF", size=10), xanchor="left")
            fig_vec.add_annotation(x=max(max_v, ref_v*1.2)*0.98, y=min_q*1.05, text="🌪️ Volume Forçado", showarrow=False, font=dict(color="#FFA500", size=10), xanchor="right")
            fig_vec.add_annotation(x=min_v*1.05, y=min_q*1.05, text="⚠️ Inoperante", showarrow=False, font=dict(color="#FF4B4B", size=10), xanchor="left")

            # Vetor direcional com seta conectando Base a Alvo
            fig_vec.add_annotation(
                x=v_target, y=q_target,
                ax=v_base, ay=q_base,
                xref="x", yref="y", axref="x", ayref="y",
                text="", showarrow=True,
                arrowhead=3, arrowsize=1.5, arrowwidth=2.5,
                arrowcolor="#FFFF00"
            )

            # Pontos Base e Alvo com hover informativo
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

        # Decomposição Espacial por Zona
        st.markdown("##### 3. Onde a Qualidade Mudou? (Decomposição por Zona de Chute)")
        st.caption("Compara a disciplina de finalização na Pequena Área, Grande Área e Fora da Área.")

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

        # Conclusão Textual Direta
        predominance = "Qualidade da Finalização (chutes em posições melhores)" if abs(effect_quality) > abs(effect_volume) else "Volume de Finalizações (capacidade de arrematar com maior frequência)"
        direction = "aumento" if delta_xg90 > 0 else "queda"
        st.success(
            f"**Diagnóstico Waterfall:** Na transição de **{label_base}** para **{label_target}**, o Palmeiras registrou um {direction} de "
            f"**{abs(delta_xg90):.2f} no xG/90** (de {xg90_base:.2f} para {xg90_target:.2f}). "
            f"O motor preponderante foi a **{predominance}** (impacto de {effect_quality:+.2f} da qualidade vs {effect_volume:+.2f} do volume)."
        )

    # -------------------------------------------------------------------------
    # ABA 2: ANATOMIA DOS GOLS & DEFESA (POR QUE GANHA/PERDE?)
    # -------------------------------------------------------------------------
    with t_diag2:
        st.markdown("#### 🎯 Por que o Time Vence ou Perde Mais? (Anatomia Causal dos Resultados)")
        st.markdown(
            "> **🎯 As Perguntas Fundamentais:**<br>"
            "1. *Se o xG aumentou, por que os gols reais não subiram na mesma proporção (ou caíram)?*<br>"
            "2. *Por que o aproveitamento de vitórias subiu ou caiu se o time produziu xG? (O Balanço Ofensivo-Defensivo)*",
            unsafe_allow_html=True
        )

        # Métricas de Gols e Defesa
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

        eff_conv_b = (gols_pro_b / xg_total_base - 1.0) * 100 if xg_total_base > 0 else 0
        eff_conv_t = (gols_pro_t / xg_total_target - 1.0) * 100 if xg_total_target > 0 else 0

        vits_b = (m_base["result"] == "Vitória").sum()
        vits_t = (m_target["result"] == "Vitória").sum()
        derrs_b = (m_base["result"] == "Derrota").sum()
        derrs_t = (m_target["result"] == "Derrota").sum()
        aprov_b = (vits_b * 3 + (m_base["result"] == "Empate").sum()) / (n_m_base * 3) * 100
        aprov_t = (vits_t * 3 + (m_target["result"] == "Empate").sum()) / (n_m_target * 3) * 100

        # Cards do Balanço Ataque vs Defesa
        c_ca1, c_ca2, c_ca3, c_ca4 = st.columns(4)
        c_ca1.metric(
            "Gols Marcados / Jogo",
            f"{gp_per90_t:.2f}",
            f"{gp_per90_t - gp_per90_b:+.2f} vs Base ({gp_per90_b:.2f})"
        )
        c_ca2.metric(
            "Eficiência da Finalização (G vs xG)",
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

        c_cau1, c_cau2 = st.columns([1.1, 1.1])

        with c_cau1:
            st.markdown("##### 1. A Ponte entre xG Gerado e Gols Reais (Ataque)")
            st.caption("Compara a expectativa de gols criada (xG) com a conversão real das redes.")

            bridge_df = pd.DataFrame({
                "Métrica": ["xG / 90 min (Criação)", "Gols Reais / 90 min (Rede)"],
                label_base: [round(xg90_base, 2), round(gp_per90_b, 2)],
                label_target: [round(xg90_target, 2), round(gp_per90_t, 2)]
            })
            bridge_melted = pd.melt(bridge_df, id_vars=["Métrica"], var_name="Período", value_name="Média/Jogo")

            fig_bridge = px.bar(
                bridge_melted, x="Métrica", y="Média/Jogo", color="Período",
                barmode="group", text="Média/Jogo",
                color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                template="plotly_dark"
            )
            fig_bridge.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_bridge, use_container_width=True)

        with c_cau2:
            st.markdown("##### 2. Balanço Ofensivo vs. Defensivo (xG Pró vs xG Contra)")
            st.caption("Futebol é uma balança de duas vias. Subir o ataque mas abrir a defesa custa vitórias.")

            bal_df = pd.DataFrame({
                "Período": [label_base, label_target],
                "xG Pró / Jogo": [round(xg90_base, 2), round(xg90_target, 2)],
                "xG Sofrido / Jogo": [round(xgc_per90_b, 2), round(xgc_per90_t, 2)],
                "Saldo xG": [round(saldo_xg_b, 2), round(saldo_xg_t, 2)]
            })

            fig_bal = go.Figure()
            fig_bal.add_trace(go.Bar(
                x=bal_df["Período"], y=bal_df["xG Pró / Jogo"],
                name="xG Pró (Ataque)", marker_color="#00FF87",
                text=bal_df["xG Pró / Jogo"], textposition="outside"
            ))
            fig_bal.add_trace(go.Bar(
                x=bal_df["Período"], y=bal_df["xG Sofrido / Jogo"],
                name="xG Sofrido (Defesa)", marker_color="#FF4B4B",
                text=bal_df["xG Sofrido / Jogo"], textposition="outside"
            ))
            fig_bal.update_layout(
                template="plotly_dark", height=340, barmode="group",
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_bal, use_container_width=True)

        st.markdown("---")

        # Diagnóstico Causal Didático
        st.markdown("##### 3. Diagnóstico Causal em Linguagem Natural")

        # Análise de conversão
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

        # Análise defensiva e resultado
        delta_def = xgc_per90_t - xgc_per90_b
        if delta_def > 0.20:
            def_text = (
                f"No aspecto defensivo, a equipe ficou significativamente **mais exposta**: concedeu **{xgc_per90_t:.2f} xG sofrido por jogo** "
                f"no alvo contra **{xgc_per90_b:.2f}** na base ({delta_def:+.2f} xG/jogo a mais para o adversário). "
                f"Essa maior concessão de chances no campo de defesa explica a oscilação de vitórias (aproveitamento foi de {aprov_b:.1f}% para {aprov_t:.1f}%)."
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
            st.caption("Participação percentual de cada faixa longitudinal nas finalizações do time.")

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
            st.caption("Pequena Área (letalidade máxima) vs Grande Área vs Fora da Área.")

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

        # Agregar métricas individuais por período
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

        # Filtrar atletas com alguma relevância (pelo menos 3 chutes)
        top_players = pm[pm["chutes_total"] >= 3].sort_values(by="xg_total_ambos", ascending=False).copy()

        # Destaques em Cards
        if not top_players.empty:
            most_growth_xg = pm.sort_values(by="delta_xg", ascending=False).iloc[0]
            most_growth_gols = pm.sort_values(by="delta_gols", ascending=False).iloc[0]
            most_drop_xg = pm.sort_values(by="delta_xg", ascending=True).iloc[0]

            cd1, cd2, cd3 = st.columns(3)
            cd1.metric(
                "🚀 Maior Ganho de Criação (xG)",
                most_growth_xg["player_name"],
                f"{most_growth_xg['delta_xg']:+.2f} xG ({most_growth_xg['xg_b']:.2f} ➔ {most_growth_xg['xg_t']:.2f})"
            )
            cd2.metric(
                "🎯 Maior Salto em Gols",
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
            st.markdown("##### 1. Divergência de Conversão: Quem foi Clínico vs Quem Desperdiçou?")
            st.caption("Saldo de Gols marcados menos xG esperado (G - xG). Verde = letal; Vermelho = desperdiçou.")

            # Mostrar eficiência no período Alvo para os principais finalizadores
            eff_plot = top_players[top_players["chutes_t"] >= 2].sort_values(by="diff_eff_t", ascending=True).tail(10).copy()
            if not eff_plot.empty:
                colors_eff = ["#00FF87" if v >= 0 else "#FF4B4B" for v in eff_plot["diff_eff_t"]]
                fig_diverg = go.Figure(go.Bar(
                    x=eff_plot["diff_eff_t"],
                    y=eff_plot["player_name"],
                    orientation="h",
                    marker_color=colors_eff,
                    text=eff_plot["diff_eff_t"].apply(lambda v: f"{v:+.2f}"),
                    textposition="outside"
                ))
                fig_diverg.add_vline(x=0, line_color="#888888", line_width=1.5)
                fig_diverg.update_layout(
                    template="plotly_dark", height=380,
                    margin=dict(l=10, r=10, t=30, b=10),
                    xaxis_title=f"Saldo de Letalidade (Gols - xG) em {label_target}"
                )
                st.plotly_chart(fig_diverg, use_container_width=True)
            else:
                st.info("Amostra pequena no período alvo para o gráfico de divergência.")

        with c_scat:
            st.markdown("##### 2. Mapa de Eficiência dos Finalizadores (Scatter xG vs Gols)")
            st.caption("Acima da linha diagonal tracejada = finalização clínica. Abaixo = underperformance.")

            # Montar dataset com linhas de cada atleta no período Alvo e Base
            scat_list = []
            for _, r in top_players.iterrows():
                if r["chutes_b"] >= 2:
                    scat_list.append({"Atleta": r["player_name"], "xG": r["xg_b"], "Gols": r["gols_b"], "Chutes": r["chutes_b"], "Período": label_base})
                if r["chutes_t"] >= 2:
                    scat_list.append({"Atleta": r["player_name"], "xG": r["xg_t"], "Gols": r["gols_t"], "Chutes": r["chutes_t"], "Período": label_target})
            scat_df = pd.DataFrame(scat_list)

            if not scat_df.empty:
                max_axis = max(scat_df["xG"].max(), scat_df["Gols"].max()) * 1.25

                # Rotular apenas os atletas de maior destaque para evitar sobreposições
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
                    x=[0, max_axis], y=[0, max_axis], mode="lines",
                    name="Paridade Esperada (G = xG)",
                    line=dict(color="#777777", dash="dash", width=1.5)
                ))
                fig_scat_fin.update_traces(textposition="top center")
                fig_scat_fin.update_layout(
                    template="plotly_dark", height=380,
                    margin=dict(l=10, r=10, t=30, b=10),
                    xaxis=dict(title="Gols Esperados (xG Acumulado)", range=[0, max_axis]),
                    yaxis=dict(title="Gols Reais Marcados", range=[0, max_axis]),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_scat_fin, use_container_width=True)

        st.markdown("---")

        # Tabela Comparativa de Deltas
        st.markdown("##### 3. Balanço Completo da Evolução dos Jogadores (Deltas)")
        st.caption("Ordenado pelos atletas de maior volume de criação somado.")

        disp_players = top_players[[
            "player_name", "xg_b", "xg_t", "delta_xg", "gols_b", "gols_t", "delta_gols", "diff_eff_t"
        ]].rename(columns={
            "player_name": "Atleta",
            "xg_b": f"xG ({label_base})",
            "xg_t": f"xG ({label_target})",
            "delta_xg": "Δ xG",
            "gols_b": f"Gols ({label_base})",
            "gols_t": f"Gols ({label_target})",
            "delta_gols": "Δ Gols",
            "diff_eff_t": f"Saldo Letalidade (G - xG)"
        })

        st.dataframe(
            disp_players.head(15),
            use_container_width=True,
            hide_index=True
        )

    # -------------------------------------------------------------------------
    # ABA 5: FORMAÇÕES TÁTICAS, FIELD TILT & PRANCHETA INTERATIVA
    # -------------------------------------------------------------------------
    with t_diag5:
        st.markdown("#### 🛡️ Formações Táticas, Domínio Territorial (Field Tilt) & Prancheta Interativa")

        # Banner Front-and-Center de Field Tilt
        st.markdown(
            """
            <div style="background-color: #1A2332; border: 1px solid #2A3B50; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;">
                <h4 style="color: #00FF87; margin-top: 0; margin-bottom: 8px;">📖 O que é Field Tilt (% de Domínio Territorial)?</h4>
                <p style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.5; margin-bottom: 10px;">
                    O <b>Field Tilt</b> mede a porcentagem de entradas e ações realizadas no <b>terço ofensivo</b> do campo em relação ao rival:
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
            "> **🎯 A Pergunta Central:** *Linha de 4 (ex: 4-2-3-1, 4-3-3) vs Linha de 3/5 (ex: 3-4-2-1, 3-5-2): "
            "Qual estrutura de Abel Ferreira gerou maior dominância territorial e melhor saldo de chances criadas?*"
        )

        if "palmeiras_formation" not in m_dataset.columns or "field_tilt" not in m_dataset.columns:
            st.warning("⚠️ Dados estruturais de formação e Field Tilt ainda não estão carregados.")
            return

        # Filtro de Amostra das Formações
        tab5_seasons = st.multiselect(
            "Filtrar Temporadas em Análise para as Formações:",
            all_seasons, default=all_seasons, key="diag_uni_tab5_seasons"
        )

        form_df = m_dataset[
            (m_dataset["season"].isin(tab5_seasons)) &
            (m_dataset["palmeiras_formation"].notna()) & 
            (m_dataset["palmeiras_formation"] != "Desconhecida")
        ].copy()

        form_df["familia_tatica"] = form_df["palmeiras_formation"].apply(
            lambda f: "Linha de 3/5 Zagueiros" if str(f).startswith(("3-", "5-")) else "Linha de 4 Defensores"
        )

        # 1. Duelo Estrutural: Linha de 4 vs Linha de 3/5
        st.markdown("##### 1. Duelo Estrutural: Linha de 4 vs. Linha de 3/5 Zagueiros")

        fam_agg = form_df.groupby("familia_tatica").agg(
            partidas=("match_id", "count"),
            vitorias=("result", lambda s: (s == "Vitória").sum()),
            aproveitamento=("result", lambda s: ((s == "Vitória").sum() * 3 + (s == "Empate").sum()) / (len(s) * 3) * 100),
            xg_pro=("palmeiras_xg", "mean"),
            xg_contra=("opponent_xg", "mean"),
            field_tilt=("field_tilt", "mean"),
            toques_area=("palmeiras_touches_in_box", "mean"),
            posse=("palmeiras_possession", "mean")
        ).reset_index()
        fam_agg["saldo_xg"] = fam_agg["xg_pro"] - fam_agg["xg_contra"]

        c_f1, c_f2 = st.columns(2)
        for i, row in fam_agg.iterrows():
            with (c_f1 if i == 0 else c_f2):
                border_col = "#00FF87" if "Linha de 4" in row["familia_tatica"] else "#00BFFF"
                st.markdown(
                    f"""
                    <div style="border: 2px solid {border_col}; border-radius: 8px; padding: 14px; background: #18202C; margin-bottom: 15px;">
                        <h4 style="margin: 0 0 10px 0; color: {border_col};">{row['familia_tatica']}</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.92rem;">
                            <div><b>Amostra:</b> {row['partidas']} jogos</div>
                            <div><b>Aproveitamento:</b> {row['aproveitamento']:.1f}%</div>
                            <div><b>Field Tilt Médio:</b> {row['field_tilt']:.1f}%</div>
                            <div><b>Posse Média:</b> {row['posse']:.1f}%</div>
                            <div><b>xG Pró / Jogo:</b> {row['xg_pro']:.2f}</div>
                            <div><b>xG Sofrido / Jogo:</b> {row['xg_contra']:.2f}</div>
                            <div><b>Saldo xG:</b> <span style="color: {'#00FF87' if row['saldo_xg']>0 else '#FF4B4B'}">{row['saldo_xg']:+.2f}</span></div>
                            <div><b>Toques na Área:</b> {row['toques_area']:.1f} / jogo</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("---")

        # 2. Matriz de Dominância e Penetração
        st.markdown("##### 2. Matriz de Dominância & Mecânica de Penetração")

        form_counts = form_df["palmeiras_formation"].value_counts()
        valid_formations = form_counts[form_counts >= 3].index.tolist()
        form_filtered = form_df[form_df["palmeiras_formation"].isin(valid_formations)].copy()

        if not form_filtered.empty:
            f_agg = form_filtered.groupby("palmeiras_formation").agg(
                partidas=("match_id", "count"),
                vitorias=("result", lambda s: (s == "Vitória").sum()),
                xg_pro=("palmeiras_xg", "mean"),
                xg_contra=("opponent_xg", "mean"),
                field_tilt=("field_tilt", "mean"),
                toques_area=("palmeiras_touches_in_box", "mean"),
                cruzamentos=("palmeiras_crosses_attempted", "mean"),
                through_balls=("palmeiras_through_balls", "mean"),
                posse=("palmeiras_possession", "mean")
            ).reset_index()

            f_agg["vit_pct"] = (f_agg["vitorias"] / f_agg["partidas"] * 100).round(1)
            f_agg["saldo_xg"] = (f_agg["xg_pro"] - f_agg["xg_contra"]).round(2)
            f_agg["xg_pro"] = f_agg["xg_pro"].round(2)
            f_agg["xg_contra"] = f_agg["xg_contra"].round(2)
            f_agg["field_tilt"] = f_agg["field_tilt"].round(1)
            f_agg["toques_area"] = f_agg["toques_area"].round(1)
            f_agg["cruzamentos"] = f_agg["cruzamentos"].round(1)
            f_agg["through_balls"] = f_agg["through_balls"].round(2)
            f_agg["posse"] = f_agg["posse"].round(1)

            c_sc1, c_sc2 = st.columns([1.1, 1.1])

            with c_sc1:
                st.markdown("###### Matriz: Field Tilt vs. Saldo de xG por Esquema")
                fig_mat = px.scatter(
                    f_agg, x="field_tilt", y="saldo_xg", size="partidas", color="vit_pct",
                    text="palmeiras_formation",
                    hover_data={"palmeiras_formation": True, "partidas": True, "field_tilt": ":.1f", "saldo_xg": ":+.2f", "vit_pct": ":.1f", "toques_area": ":.1f"},
                    color_continuous_scale="Viridis", template="plotly_dark",
                    labels={"field_tilt": "Field Tilt Médio (% Ocupação)", "saldo_xg": "Saldo de xG", "vit_pct": "% Vitórias"}
                )
                fig_mat.add_vline(x=50.0, line_dash="dash", line_color="#777777")
                fig_mat.add_hline(y=0.0, line_dash="dash", line_color="#777777")
                fig_mat.update_traces(textposition="top center")
                fig_mat.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_mat, use_container_width=True)

            with c_sc2:
                st.markdown("###### Penetração: Cruzamentos vs. Passes em Profundidade")
                st.caption("Apresentados em subplots independentes com escalas corretas.")

                from plotly.subplots import make_subplots
                fig_pen = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
                                        subplot_titles=("Cruzamentos Tentados / Jogo (Aéreo)", "Passes em Profundidade / Jogo (Ruptura)"))
                
                fig_pen.add_trace(go.Bar(
                    x=f_agg["palmeiras_formation"], y=f_agg["cruzamentos"],
                    name="Cruzamentos", marker_color="#FFA500",
                    text=f_agg["cruzamentos"], textposition="outside"
                ), row=1, col=1)

                fig_pen.add_trace(go.Bar(
                    x=f_agg["palmeiras_formation"], y=f_agg["through_balls"],
                    name="Passes em Profundidade", marker_color="#00FF87",
                    text=f_agg["through_balls"], textposition="outside"
                ), row=2, col=1)

                fig_pen.update_layout(template="plotly_dark", height=360, margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
                st.plotly_chart(fig_pen, use_container_width=True)

            # Tabela Formatada de Esquemas
            st.markdown("##### 3. Tabela Comparativa Detalhada por Formação")
            disp_form = f_agg.rename(columns={
                "palmeiras_formation": "Formação",
                "partidas": "Jogos",
                "vit_pct": "Vitórias (%)",
                "xg_pro": "xG Pró / Jogo",
                "xg_contra": "xG Contra / Jogo",
                "saldo_xg": "Saldo xG",
                "field_tilt": "Field Tilt Médio (%)",
                "toques_area": "Toques Área / Jogo",
                "cruzamentos": "Cruzamentos / Jogo",
                "through_balls": "Passes Profundidade / Jogo",
                "posse": "Posse Média (%)"
            })
            st.dataframe(disp_form.sort_values(by="Jogos", ascending=False), use_container_width=True, hide_index=True)

        st.markdown("---")

        # ---------------------------------------------------------------------
        # 3. PRANCHETA TÁTICA & VERIFICADOR DE ESCALAÇÕES EM CAMPO
        # ---------------------------------------------------------------------
        st.markdown("##### 🏟️ 4. Prancheta Tática & Verificador de Escalações em Campo")
        st.markdown(
            "> *\"Nem sempre o SofaScore detecta corretamente qual a formação em campo e gostaria de conferir.\"*<br>"
            "Aqui você pode selecionar qualquer formação para visualizar a prancheta de posicionamento no gramado "
            "e inspecionar as partidas reais disputadas para **conferir os 11 titulares escalados em campo**.",
            unsafe_allow_html=True
        )

        all_valid_forms = valid_formations if not form_filtered.empty else ["4-2-3-1", "3-4-2-1", "3-5-2", "4-4-2", "4-3-3"]
        
        c_pf1, c_pf2 = st.columns([1, 2])
        with c_pf1:
            sel_form = st.selectbox("Selecione a Formação Tática:", all_valid_forms, key="board_sel_form")
            board_mode = st.radio(
                "Modo de Visualização:",
                ["📐 Gabarito Tático Teórico", "🔍 Conferir Jogo Real no Campo"],
                key="board_mode_radio"
            )

        with c_pf2:
            real_players = None
            match_info = None

            if board_mode == "🔍 Conferir Jogo Real no Campo":
                # Buscar todas as partidas com essa formação
                matches_with_form = form_df[form_df["palmeiras_formation"] == sel_form].sort_values(by="date", ascending=False)
                if matches_with_form.empty:
                    st.info(f"Nenhum jogo recente com a formação {sel_form} no filtro.")
                else:
                    match_opts = {}
                    for _, r in matches_with_form.iterrows():
                        key_str = f"{r['date']} - {r['tournament']}: {r['home_team']} {r['home_score']}x{r['away_score']} {r['away_team']} ({r['result']})"
                        match_opts[key_str] = r

                    chosen_match_label = st.selectbox(
                        f"Selecione uma partida ({len(match_opts)} disponíveis):",
                        list(match_opts.keys()),
                        key="board_match_picker"
                    )
                    chosen_row = match_opts[chosen_match_label]
                    match_info = chosen_row

                    # Carregar escalação real do JSON em data/raw/
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

            # Função de desenho da Prancheta Tática
            def draw_tactical_pitch(formation, players_list=None):
                fig = go.Figure()
                # Campo de futebol com proporção e marcações
                fig.add_shape(type="rect", x0=2, y0=2, x1=98, y1=98, line=dict(color="#FFFFFF", width=2), fillcolor="#183624")
                fig.add_shape(type="line", x0=2, y0=50, x1=98, y1=50, line=dict(color="#FFFFFF", width=1.5))
                fig.add_shape(type="circle", x0=38, y0=38, x1=62, y1=62, line=dict(color="#FFFFFF", width=1.5))
                fig.add_shape(type="circle", x0=49.2, y0=49.2, x1=50.8, y1=50.8, fillcolor="#FFFFFF", line_color="#FFFFFF")

                # Área de defesa (Palmeiras)
                fig.add_shape(type="rect", x0=22, y0=2, x1=78, y1=22, line=dict(color="#FFFFFF", width=1.5))
                fig.add_shape(type="rect", x0=36, y0=2, x1=64, y1=9, line=dict(color="#FFFFFF", width=1.5))
                fig.add_shape(type="circle", x0=49.3, y0=13.3, x1=50.7, y1=14.7, fillcolor="#FFFFFF", line_color="#FFFFFF")

                # Área de ataque (Adversário)
                fig.add_shape(type="rect", x0=22, y0=78, x1=78, y1=98, line=dict(color="#FFFFFF", width=1.5))
                fig.add_shape(type="rect", x0=36, y0=91, x1=64, y1=98, line=dict(color="#FFFFFF", width=1.5))
                fig.add_shape(type="circle", x0=49.3, y0=85.3, x1=50.7, y1=86.7, fillcolor="#FFFFFF", line_color="#FFFFFF")

                # Coordenadas dos 11 jogadores
                try:
                    lines = [int(x) for x in str(formation).split('-')]
                except Exception:
                    lines = [4, 4, 2]
                coords = [(50, 8)] # GK
                n_lines = len(lines)
                y_positions = [22 + i * (66 / max(1, n_lines - 1)) for i in range(n_lines)]

                for idx, (count, y) in enumerate(zip(lines, y_positions)):
                    if count == 1:
                        xs = [50]
                    elif count == 2:
                        xs = [36, 64]
                    elif count == 3:
                        xs = [26, 50, 74] if idx == 0 else [16, 50, 84]
                    elif count == 4:
                        xs = [14, 38, 62, 86]
                    elif count == 5:
                        xs = [12, 31, 50, 69, 88]
                    else:
                        xs = [15 + j * (70 / (count - 1)) for j in range(count)]
                    for x in xs:
                        coords.append((round(x, 1), round(y, 1)))

                xs = [c[0] for c in coords[:11]]
                ys = [c[1] for c in coords[:11]]

                if players_list and len(players_list) >= 11:
                    labels = [f"<b>{p.get('shirtNumber', '')}</b><br>{p.get('name', '').split()[-1]}" for p in players_list[:11]]
                    hover_texts = [f"#{p.get('shirtNumber', '')} {p.get('name', '')} ({p.get('position', '')})" for p in players_list[:11]]
                else:
                    role_labels = ["GOL", "LAT/ZAG", "ZAG", "ZAG", "LAT/ZAG", "VOL", "VOL", "MEI/PNT", "MEI", "MEI/PNT", "ATA"]
                    labels = [f"<b>{role_labels[i] if i < len(role_labels) else 'JOG'}</b>" for i in range(len(coords[:11]))]
                    hover_texts = labels

                fig.add_trace(go.Scatter(
                    x=xs, y=ys,
                    mode="markers+text",
                    marker=dict(size=26, color="#00FF87", line=dict(color="#0A1E11", width=2)),
                    text=labels,
                    textposition="top center",
                    textfont=dict(color="#FFFFFF", size=10),
                    hovertext=hover_texts,
                    hoverinfo="text"
                ))

                fig.update_layout(
                    template="plotly_dark",
                    height=500,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 100]),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 100], scaleanchor="x", scaleratio=1),
                    showlegend=False
                )
                return fig

            fig_board = draw_tactical_pitch(sel_form, real_players)
            st.plotly_chart(fig_board, use_container_width=True)

            if match_info is not None and real_players is not None:
                st.markdown(
                    f"**Conferência da Escalação:** {match_info['tournament']} | Data: {match_info['date']} | "
                    f"Placar: **{match_info['palmeiras_score']}x{match_info['opponent_score']}** vs {match_info['opponent_name']} | "
                    f"Posse: {match_info['palmeiras_possession']:.1f}% | Field Tilt: {match_info['field_tilt']:.1f}%"
                )
                st.caption(f"Titulares ({len(real_players)}): " + ", ".join([f"{p['name']} (#{p['shirtNumber']})" for p in real_players]))

    # =========================================================================
    # GUIA METODOLÓGICO EXPANDÍVEL NO RODAPÉ
    # =========================================================================
    with st.expander("📖 Guia Metodológico & Formulações Matemáticas (Consulta Aprofundada)", expanded=False):
        st.markdown(r"""
        ### 🎯 Qual pergunta cada análise responde?
        1. **Decomposição Fatorial Waterfall:** Responde se o Palmeiras melhorou ou piorou por volume (mais chutes) ou por qualidade (melhor pontaria e seleção de jogadas).
           $$\\Delta xG_{90} = \\Delta V \\cdot \\bar{Q} + \\bar{V} \\cdot \\Delta Q$$
        2. **Anatomia Causal dos Resultados:** Separa o efeito de criação ($xG$) da letalidade ($Gols/xG$) e investiga o balanço defensivo ($xG$ sofrido e exposição da zaga) para explicar por que o time venceu ou perdeu mais jogos.
        3. **Vetor de Deslocamento Tático:** Posiciona a equipe em 4 quadrantes ofensivos (Ataque de Elite, Clínico, Volume Forçado, Inoperante) e traça uma trajetória vetorial indicando a evolução no tempo.
        4. **Field Tilt (%):** Proporção de ações no terço ofensivo em relação ao adversário. Revela dominância territorial verdadeira, livre da armadilha de posse passiva na defesa.
        5. **Prancheta Tática & Verificador de Escalações:** Permite ao usuário conferir diretamente a fidedignidade da detecção do SofaScore inspecionando os 11 titulares em qualquer partida da história recente.
        """)
'''

with open("app/modules/mod6_tactical_diagnosis.py", "w", encoding="utf-8") as f:
    f.write(code)

print("mod6_tactical_diagnosis.py written successfully!")
