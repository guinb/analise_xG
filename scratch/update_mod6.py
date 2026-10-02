# -*- coding: utf-8 -*-
"""
Script to generate app/modules/mod6_tactical_diagnosis.py
"""

code = '''"""
Módulo 6: Diagnóstico Tático & O que Mudou?
Responde a perguntas cruciais sobre a evolução do Palmeiras sob Abel Ferreira:
1. O que influenciou para o xG subir ou descer? (Decomposição Fatorial Waterfall + Vetor Tático)
2. O posicionamento mudou? (Análise de corredores esquerdo/centro/direito, zonas e proximidade ao gol)
3. O estilo de jogo mudou? (Identidade de criação: posse em jogo aberto vs bola parada vs transições)
4. Quem explica as oscilações? (Eficiência de finalizadores e transferência de protagonismo)
5. Formações táticas e domínio territorial (Field Tilt e Linha de 4 vs Linha de 3)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def render_tactical_diagnosis_tab(df_shots: pd.DataFrame, df_matches: pd.DataFrame, df_shots_full: pd.DataFrame = None, df_matches_full: pd.DataFrame = None):
    st.markdown("### 🧠 Módulo: Diagnóstico Tático & O que Mudou?")

    st.info(
        "💡 **Eleve o Debate Tático:** Para responder se o estilo e o posicionamento mudaram e entender as causas da variação do xG, "
        "não basta olhar números estáticos isolados. Aqui decompomos as forças matemáticas (Efeito Volume vs Efeito Qualidade), "
        "o mapa de calor dos corredores laterais/centrais, a evolução dos protagonistas e a dominância territorial (Field Tilt) "
        "ao longo das temporadas e turnos sob o comando de Abel Ferreira."
    )

    # Utilizar a base histórica completa por padrão para garantir que todas as temporadas e turnos estejam acessíveis
    m_dataset = df_matches_full if df_matches_full is not None and not df_matches_full.empty else df_matches
    s_dataset = df_shots_full if df_shots_full is not None and not df_shots_full.empty else df_shots
    pal_shots_all = s_dataset[s_dataset["is_palmeiras"] == True].copy()

    if pal_shots_all.empty or m_dataset.empty:
        st.warning("Nenhum dado disponível para análise tática.")
        return

    # =========================================================================
    # PAINEL UNIFICADO DE COMPARAÇÃO (GLOBAL PARA TODAS AS ABAS DO MÓDULO)
    # =========================================================================
    st.markdown("#### 🎯 Painel Unificado de Comparação Tática")
    st.caption("Selecione o recorte desejado abaixo. Esta escolha alimentará automaticamente **todas as 4 abas** a seguir.")

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
                # Sugere penúltima temporada como base se houver mais de uma
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
    s_base = pal_shots_all[pal_shots_all["match_id"].isin(m_base["match_id"])]
    s_target = pal_shots_all[pal_shots_all["match_id"].isin(m_target["match_id"])]

    n_m_base = m_base["match_id"].nunique()
    n_m_target = m_target["match_id"].nunique()
    n_s_base = len(s_base)
    n_s_target = len(s_target)

    # Banner de Contexto da Comparação Ativa
    st.markdown(
        f"""
        <div style="background-color: #1E2530; padding: 12px 18px; border-radius: 8px; border-left: 5px solid #00FF87; margin-bottom: 20px;">
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
        st.warning(f"⚠️ Dados insuficientes para efetuar a comparação entre '{label_base}' ({n_m_base} jogos) e '{label_target}' ({n_m_target} jogos). Selecione outros recortes acima.")
        return

    # Cálculos matemáticos estruturados compartilhados
    # Métricas Base
    v_base = n_s_base / n_m_base
    xg_total_base = s_base["xg"].sum()
    q_base = xg_total_base / n_s_base if n_s_base > 0 else 0
    xg90_base = xg_total_base / n_m_base

    # Métricas Alvo
    v_target = n_s_target / n_m_target
    xg_total_target = s_target["xg"].sum()
    q_target = xg_total_target / n_s_target if n_s_target > 0 else 0
    xg90_target = xg_total_target / n_m_target

    delta_xg90 = xg90_target - xg90_base
    delta_v = v_target - v_base
    delta_q = q_target - q_base

    # Decomposição exata: Delta xG = Delta V * mean(Q) + mean(V) * Delta Q
    mean_q = (q_base + q_target) / 2.0
    mean_v = (v_base + v_target) / 2.0
    effect_volume = delta_v * mean_q
    effect_quality = mean_v * delta_q

    # =========================================================================
    # ABAS DO MÓDULO 6 (CONSUMINDO A COMPARAÇÃO UNIFICADA)
    # =========================================================================
    t_diag1, t_diag2, t_diag3, t_diag4 = st.tabs([
        "🌊 1. Decomposição Fatorial (O que Mudou no xG?)",
        "📐 2. Posicionamento & Onde Chutou (Geometria)",
        "🧩 3. Identidade Tática & Protagonistas (Quem Fez?)",
        "🛡️ 4. Formações Táticas & Domínio Territorial (Field Tilt)"
    ])

    # -------------------------------------------------------------------------
    # ABA 1: DECOMPOSIÇÃO FATORIAL WATERFALL & VETOR TÁTICO
    # -------------------------------------------------------------------------
    with t_diag1:
        st.markdown("#### 🌊 O que Fez o xG Subir ou Descer?")
        st.markdown(
            "> **🎯 A Pergunta Central:** *O Palmeiras gerou mais ou menos perigo de gol porque passou a finalizar mais vezes (Volume) "
            "ou porque foi capaz de criar chances mais claras de finalização (Qualidade)?*"
        )

        # Cards com métricas principais
        k1, k2, k3, k4 = st.columns(4)
        k1.metric(f"xG/90 ({label_base})", f"{xg90_base:.2f}", f"{v_base:.1f} chutes/90 | {q_base:.3f} xG/chute")
        k2.metric(f"xG/90 ({label_target})", f"{xg90_target:.2f}", f"{delta_xg90:+.2f} ({v_target:.1f} chutes/90)")
        k3.metric("Efeito Volume (Qtd Chutes)", f"{effect_volume:+.2f} xG/90", f"{delta_v:+.1f} chutes/90")
        k4.metric("Efeito Qualidade (Seleção)", f"{effect_quality:+.2f} xG/90", f"{delta_q:+.3f} xG/chute")

        st.markdown("---")

        c_g1, c_g2 = st.columns([1.1, 1.1])

        with c_g1:
            st.markdown("##### 1. Decomposição Waterfall (Forças Matemáticas)")
            st.caption("Isola rigorosamente quanto do xG veio de chutar mais vezes vs chutar de posições melhores.")

            fig_wf = go.Figure(go.Waterfall(
                name="Decomposição xG",
                orientation="v",
                measure=["absolute", "relative", "relative", "total"],
                x=[f"Base: {label_base}", "Efeito Volume (Qtd)", "Efeito Qualidade (Seleção)", f"Alvo: {label_target}"],
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
                height=400,
                margin=dict(l=10, r=10, t=30, b=10),
                yaxis_title="xG / 90 minutos"
            )
            st.plotly_chart(fig_wf, use_container_width=True)

        with c_g2:
            st.markdown("##### 2. Deslocamento Vetorial Tático (Volume vs Qualidade)")
            st.caption("Matriz de eficiência ofensiva em 4 quadrantes. A seta indica para onde o time migrou.")

            # Limites e referências para os quadrantes
            max_v = max(v_base, v_target) * 1.25
            max_q = max(q_base, q_target) * 1.25
            ref_v = 14.5  # Média de chutes típica da Série A
            ref_q = 0.105 # xG médio por chute da Série A

            fig_vec = go.Figure()

            # Linhas de referência dos quadrantes
            fig_vec.add_vline(x=ref_v, line_dash="dash", line_color="#555555", annotation_text="Média Chutes", annotation_position="top left")
            fig_vec.add_hline(y=ref_q, line_dash="dash", line_color="#555555", annotation_text="Média xG/Chute", annotation_position="bottom right")

            # Quadrantes anotados
            fig_vec.add_annotation(x=ref_v * 1.15, y=ref_q * 1.15, text="🔥 Ataque de Elite<br>(Alto Volume & Alta Qualidade)", showarrow=False, font=dict(color="#00FF87", size=10), opacity=0.8)
            fig_vec.add_annotation(x=ref_v * 0.85, y=ref_q * 1.15, text="🎯 Clínico / Letal<br>(Pouco Volume, Alta Seleção)", showarrow=False, font=dict(color="#00BFFF", size=10), opacity=0.8)
            fig_vec.add_annotation(x=ref_v * 1.15, y=ref_q * 0.85, text="🌪️ Volume Forçado<br>(Chutes Desesperados / Baixo xG)", showarrow=False, font=dict(color="#FFA500", size=10), opacity=0.8)
            fig_vec.add_annotation(x=ref_v * 0.85, y=ref_q * 0.85, text="⚠️ Inoperante<br>(Baixo Volume & Baixa Qualidade)", showarrow=False, font=dict(color="#FF4B4B", size=10), opacity=0.8)

            # Vetor de transição (seta do período base para o período alvo)
            fig_vec.add_annotation(
                x=v_target, y=q_target,
                ax=v_base, ay=q_base,
                xref="x", yref="y", axref="x", ayref="y",
                text="", showarrow=True,
                arrowhead=3, arrowsize=1.5, arrowwidth=2.5,
                arrowcolor="#FFFF00"
            )

            # Pontos Base e Alvo
            fig_vec.add_trace(go.Scatter(
                x=[v_base], y=[q_base],
                mode="markers+text",
                name=f"Base: {label_base}",
                marker=dict(color="#00BFFF", size=16, symbol="circle", line=dict(color="#FFFFFF", width=2)),
                text=[f"Base: {label_base}"],
                textposition="bottom center"
            ))
            fig_vec.add_trace(go.Scatter(
                x=[v_target], y=[q_target],
                mode="markers+text",
                name=f"Alvo: {label_target}",
                marker=dict(color="#00FF87", size=18, symbol="diamond", line=dict(color="#FFFFFF", width=2)),
                text=[f"Alvo: {label_target}"],
                textposition="top center"
            ))

            fig_vec.update_layout(
                template="plotly_dark",
                height=400,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis=dict(title="Volume: Finalizações por 90 min", range=[min(v_base, v_target)*0.75, max(max_v, ref_v*1.3)]),
                yaxis=dict(title="Qualidade Média: xG por Chute", range=[min(q_base, q_target)*0.75, max(max_q, ref_q*1.3)]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_vec, use_container_width=True)

        st.markdown("---")

        # Seção: Onde a Qualidade Mudou? (Decomposição Espacial por Zonas)
        st.markdown("##### 3. Onde a Qualidade Mudou? (Decomposição por Zona de Finalização)")
        st.caption("Compara a precisão do Palmeiras na Pequena Área, Grande Área e Fora da Área entre os dois períodos.")

        # Calcular métricas por zona para Base e Alvo
        def get_zone_breakdown(df_s, n_matches, label):
            z = df_s.groupby("shot_zone").agg(
                chutes=("shot_id", "count"),
                xg_sum=("xg", "sum"),
                gols=("is_goal", "sum")
            ).reset_index()
            z["periodo"] = label
            z["chutes_por_jogo"] = (z["chutes"] / n_matches).round(2)
            z["xg_por_chute"] = (z["xg_sum"] / z["chutes"]).round(3)
            z["taxa_conversao"] = (z["gols"] / z["chutes"] * 100).round(1)
            return z

        zb_base = get_zone_breakdown(s_base, n_m_base, label_base)
        zb_target = get_zone_breakdown(s_target, n_m_target, label_target)
        zb_comb = pd.concat([zb_base, zb_target], ignore_index=True)

        cz1, cz2 = st.columns([1, 1])
        with cz1:
            fig_zb_vol = px.bar(
                zb_comb,
                x="shot_zone",
                y="chutes_por_jogo",
                color="periodo",
                barmode="group",
                text="chutes_por_jogo",
                color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                template="plotly_dark",
                labels={"shot_zone": "Zona de Finalização", "chutes_por_jogo": "Chutes / Jogo", "periodo": "Período"},
                title="Volume de Chutes por Jogo por Zona"
            )
            fig_zb_vol.update_layout(height=320, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig_zb_vol, use_container_width=True)

        with cz2:
            fig_zb_q = px.bar(
                zb_comb,
                x="shot_zone",
                y="xg_por_chute",
                color="periodo",
                barmode="group",
                text="xg_por_chute",
                color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                template="plotly_dark",
                labels={"shot_zone": "Zona de Finalização", "xg_por_chute": "xG Médio por Chute", "periodo": "Período"},
                title="Qualidade Média (xG/Chute) por Zona"
            )
            fig_zb_q.update_layout(height=320, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig_zb_q, use_container_width=True)

        # Diagnóstico em Linguagem Natural
        predominance = "Qualidade de Finalização (chutes de zonas mais perigosas e desmarcadas)" if abs(effect_quality) > abs(effect_volume) else "Volume de Finalizações (capacidade de arrematar com maior frequência)"
        direction = "aumento" if delta_xg90 > 0 else "queda"
        color_alert = "success" if delta_xg90 >= 0 else "warning"

        getattr(st, color_alert)(
            f"**Diagnóstico Conclusivo:** Ao comparar **{label_base}** com **{label_target}**, o Palmeiras registrou um {direction} de "
            f"**{abs(delta_xg90):.2f} no xG/90** (passando de {xg90_base:.2f} para {xg90_target:.2f}). "
            f"A força tática determinante para esse movimento foi a **{predominance}** "
            f"(impacto de {effect_quality:+.2f} xG/90 da qualidade vs {effect_volume:+.2f} xG/90 do volume)."
        )

    # -------------------------------------------------------------------------
    # ABA 2: POSICIONAMENTO E GEOMETRIA
    # -------------------------------------------------------------------------
    with t_diag2:
        st.markdown("#### 📐 O Posicionamento e a Geometria de Chute Mudaram?")
        st.markdown(
            "> **🎯 A Pergunta Central:** *O time de Abel Ferreira afunilou mais as jogadas pelo corredor central ou insistiu nas alas? "
            "E a disciplina de chute evoluiu: o time aproximou as finalizações da meta adversária ou arriscou de longe?*"
        )

        # Métricas geométricas comparativas
        dist_base = s_base["distance_meters"].mean()
        dist_target = s_target["distance_meters"].mean()
        ang_base = s_base["angle_degrees"].mean()
        ang_target = s_target["angle_degrees"].mean()
        in_box_base = (s_base["shot_zone"] != "Fora da Área").mean() * 100
        in_box_target = (s_target["shot_zone"] != "Fora da Área").mean() * 100

        cg1, cg2, cg3 = st.columns(3)
        cg1.metric(
            "Distância Média do Gol",
            f"{dist_target:.1f} m",
            f"{dist_target - dist_base:+.1f} m vs Base ({dist_base:.1f} m)",
            delta_color="inverse"
        )
        cg2.metric(
            "Ângulo Médio de Visão do Gol",
            f"{ang_target:.1f}°",
            f"{ang_target - ang_base:+.1f}° vs Base ({ang_base:.1f}°)"
        )
        cg3.metric(
            "% Chutes de Dentro da Área",
            f"{in_box_target:.1f}%",
            f"{in_box_target - in_box_base:+.1f}% vs Base ({in_box_base:.1f}%)"
        )

        st.markdown("---")

        cp1, cp2 = st.columns([1, 1])

        with cp1:
            st.markdown("##### 1. Ocupação dos Corredores Ofensivos (Esquerda / Centro / Direita)")
            st.caption("Percentual de todas as finalizações construídas por cada setor do gramado.")

            # Agrupar corredores
            def get_corridor_df(df_s, label):
                c = df_s.groupby("shot_corridor").agg(chutes=("shot_id", "count")).reset_index()
                c["pct"] = (c["chutes"] / c["chutes"].sum() * 100).round(1)
                c["periodo"] = label
                return c

            c_comb = pd.concat([get_corridor_df(s_base, label_base), get_corridor_df(s_target, label_target)], ignore_index=True)

            fig_corr = px.bar(
                c_comb,
                x="shot_corridor",
                y="pct",
                color="periodo",
                barmode="group",
                text=c_comb["pct"].apply(lambda p: f"{p}%"),
                color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                template="plotly_dark",
                labels={"shot_corridor": "Corredor", "pct": "% das Finalizações", "periodo": "Período"}
            )
            fig_corr.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_corr, use_container_width=True)

        with cp2:
            st.markdown("##### 2. Disciplina Espacial: Distribuição por Zona")
            st.caption("Proporção de arremates disparados na Pequena Área, Grande Área e Fora da Área.")

            def get_zone_pct(df_s, label):
                z = df_s.groupby("shot_zone").agg(chutes=("shot_id", "count")).reset_index()
                z["pct"] = (z["chutes"] / z["chutes"].sum() * 100).round(1)
                z["periodo"] = label
                return z

            z_comb = pd.concat([get_zone_pct(s_base, label_base), get_zone_pct(s_target, label_target)], ignore_index=True)

            fig_zone_p = px.bar(
                z_comb,
                x="shot_zone",
                y="pct",
                color="periodo",
                barmode="group",
                text=z_comb["pct"].apply(lambda p: f"{p}%"),
                color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                template="plotly_dark",
                labels={"shot_zone": "Zona de Finalização", "pct": "% das Finalizações", "periodo": "Período"}
            )
            fig_zone_p.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_zone_p, use_container_width=True)

        # Histograma comparativo de distância
        st.markdown("##### 3. Curva de Densidade: Distância das Finalizações ao Gol")
        st.caption("Mostra a concentração das finalizações em metros. Picos mais à esquerda representam finalizações mais próximas da meta.")

        s_base_plot = s_base.copy()
        s_base_plot["periodo"] = label_base
        s_target_plot = s_target.copy()
        s_target_plot["periodo"] = label_target
        s_both = pd.concat([s_base_plot, s_target_plot], ignore_index=True)

        fig_dist_hist = px.histogram(
            s_both,
            x="distance_meters",
            color="periodo",
            barmode="overlay",
            nbins=35,
            opacity=0.65,
            color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
            template="plotly_dark",
            labels={"distance_meters": "Distância do Gol (metros)", "periodo": "Período"}
        )
        fig_dist_hist.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="Qtd Chutes")
        st.plotly_chart(fig_dist_hist, use_container_width=True)

    # -------------------------------------------------------------------------
    # ABA 3: IDENTIDADE DE CRIAÇÃO E PROTAGONISTAS GRÁFICOS
    # -------------------------------------------------------------------------
    with t_diag3:
        st.markdown("#### 🧩 O Estilo de Jogo Mudou? (Identidade de Criação & Protagonistas)")
        st.markdown(
            "> **🎯 A Pergunta Central:** *De onde nascem os gols do Palmeiras (posse trabalhada, bola parada ou contra-ataque rápido)? "
            "E quem foram os atletas que sustentaram esse volume ofensivo na prática?*"
        )

        # 1. Composição por Fase de Criação
        st.markdown("##### 1. Identidade de Criação (% da Produção de xG por Fase)")
        st.caption("Revela o modelo de jogo: se a equipe foi mais construtora em jogo aberto, reativa em contra-ataques ou letal na bola parada.")

        def get_situation_df(df_s, label):
            sit = df_s.groupby("situation").agg(xg=("xg", "sum"), chutes=("shot_id", "count")).reset_index()
            sit["pct_xg"] = (sit["xg"] / sit["xg"].sum() * 100).round(1)
            sit["periodo"] = label
            return sit

        sit_comb = pd.concat([get_situation_df(s_base, label_base), get_situation_df(s_target, label_target)], ignore_index=True)

        fig_sit = px.bar(
            sit_comb,
            x="pct_xg",
            y="situation",
            color="periodo",
            barmode="group",
            orientation="h",
            text=sit_comb["pct_xg"].apply(lambda v: f"{v}%"),
            color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
            template="plotly_dark",
            labels={"situation": "Fase de Jogo", "pct_xg": "% do xG Total Produzido", "periodo": "Período"}
        )
        fig_sit.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_sit, use_container_width=True)

        st.markdown("---")

        # 2. Visualizações Gráficas dos Protagonistas
        st.markdown("##### 2. Quem Fez a Diferença? Análise Visual dos Finalizadores")
        st.caption("Substitui tabelas frias por visualizações analíticas de eficiência e protagonismo.")

        c_p1, c_p2 = st.columns([1.1, 1])

        with c_p1:
            st.markdown("###### Eficiência dos Finalizadores: xG Acumulado vs. Gols Marcados")
            st.caption("Linha pontilhada (y = x) representa a eficiência esperada. Acima da linha = finalização clínica/overperformance.")

            # Agregar atletas combinando os períodos com identificação
            p_base = s_base.groupby("player_name").agg(
                xg=("xg", "sum"), gols=("is_goal", "sum"), chutes=("shot_id", "count")
            ).reset_index()
            p_base["periodo"] = label_base

            p_target = s_target.groupby("player_name").agg(
                xg=("xg", "sum"), gols=("is_goal", "sum"), chutes=("shot_id", "count")
            ).reset_index()
            p_target["periodo"] = label_target

            # Filtrar quem teve ao menos 5 finalizações para evitar ruído
            p_all = pd.concat([p_base, p_target], ignore_index=True)
            p_filtered = p_all[p_all["chutes"] >= 4].copy()

            if not p_filtered.empty:
                max_val = max(p_filtered["xg"].max(), p_filtered["gols"].max()) * 1.15

                fig_eff = px.scatter(
                    p_filtered,
                    x="xg",
                    y="gols",
                    size="chutes",
                    color="periodo",
                    text="player_name",
                    hover_data={"player_name": True, "chutes": True, "xg": ":.2f", "gols": True, "periodo": True},
                    color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                    template="plotly_dark",
                    labels={"xg": "Gols Esperados (xG Acumulado)", "gols": "Gols Reais Marcados", "periodo": "Período"}
                )
                # Linha de paridade y = x
                fig_eff.add_trace(go.Scatter(
                    x=[0, max_val], y=[0, max_val],
                    mode="lines", name="Desempenho Esperado (y=x)",
                    line=dict(color="#888888", dash="dash", width=1.5),
                    showlegend=True
                ))
                fig_eff.update_traces(textposition="top center")
                fig_eff.update_layout(
                    height=380,
                    margin=dict(l=10, r=10, t=30, b=10),
                    xaxis=dict(range=[0, max_val]),
                    yaxis=dict(range=[0, max_val]),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_eff, use_container_width=True)
            else:
                st.info("Amostra pequena de atletas com mais de 4 finalizações no recorte.")

        with c_p2:
            st.markdown("###### Transferência de Protagonismo (Top Atletas em xG)")
            st.caption("Compara a centralização do perigo ofensivo entre o período Base e o Alvo.")

            # Pegar top 6 atletas somando xG nos dois períodos
            top_athletes = p_all.groupby("player_name")["xg"].sum().sort_values(ascending=False).head(7).index.tolist()
            p_top = p_all[p_all["player_name"].isin(top_athletes)].copy()
            p_top["xg"] = p_top["xg"].round(2)

            fig_top = px.bar(
                p_top,
                x="xg",
                y="player_name",
                color="periodo",
                barmode="group",
                orientation="h",
                text="xg",
                color_discrete_map={label_base: "#00BFFF", label_target: "#00FF87"},
                template="plotly_dark",
                labels={"player_name": "Atleta", "xg": "xG Acumulado", "periodo": "Período"}
            )
            fig_top.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                yaxis=dict(categoryorder="total ascending")
            )
            st.plotly_chart(fig_top, use_container_width=True)

    # -------------------------------------------------------------------------
    # ABA 4: FORMAÇÕES TÁTICAS E DOMÍNIO TERRITORIAL (FIELD TILT)
    # -------------------------------------------------------------------------
    with t_diag4:
        st.markdown("#### 🛡️ Formações Táticas & Domínio Territorial (Field Tilt)")

        # ---------------------------------------------------------------------
        # EXPLICAÇÃO DIDÁTICA DO FIELD TILT FRONT-AND-CENTER
        # ---------------------------------------------------------------------
        st.markdown(
            """
            <div style="background-color: #1A2332; border: 1px solid #2A3B50; border-radius: 10px; padding: 18px 22px; margin-bottom: 22px;">
                <h4 style="color: #00FF87; margin-top: 0; margin-bottom: 8px;">📖 O que é Field Tilt (% de Domínio Territorial)?</h4>
                <p style="color: #E2E8F0; font-size: 0.96rem; line-height: 1.55; margin-bottom: 10px;">
                    O <b>Field Tilt</b> mede a porcentagem de passes e entradas realizadas no <b>terço ofensivo</b> do campo em relação ao adversário:
                </p>
                <div style="background-color: #0F172A; padding: 10px; border-radius: 6px; text-align: center; font-family: monospace; color: #38BDF8; font-size: 1rem; margin-bottom: 12px;">
                    Field Tilt (%) = [ Entradas no Terço Ofensivo (Palmeiras) ÷ Entradas Totais no Terço Ofensivo (Palmeiras + Adversário) ] × 100
                </div>
                <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 220px; background: rgba(0,255,135,0.08); padding: 10px; border-radius: 6px; border-left: 3px solid #00FF87;">
                        <b>Por que supera a Posse Comum?</b><br>
                        <span style="font-size: 0.88rem; color: #CBD5E1;">A posse tradicional conta toques estéreis entre zagueiros no próprio campo. O Field Tilt revela onde o jogo realmente está sendo disputado e quem empurra o oponente para trás.</span>
                    </div>
                    <div style="flex: 1; min-width: 220px; background: rgba(0,191,255,0.08); padding: 10px; border-radius: 6px; border-left: 3px solid #00BFFF;">
                        <b>Escala de Interpretação:</b><br>
                        <span style="font-size: 0.88rem; color: #CBD5E1;">
                            <b>&gt; 60%:</b> Domínio sufocante (bloco adversário recuado)<br>
                            <b>50%–60%:</b> Ocupação territorial positiva<br>
                            <b>&lt; 50%:</b> Jogo reativo ou perda de meio-campo
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            "> **🎯 A Pergunta Tática Central:** *Linha de 4 (ex: 4-2-3-1, 4-3-3) vs. Linha de 3/5 (ex: 3-4-2-1, 3-5-2): "
            "Qual estrutura tática de Abel Ferreira entrega maior domínio territorial (Field Tilt) e melhor saldo de chances criadas (xG)?*"
        )

        if "palmeiras_formation" not in m_dataset.columns or "field_tilt" not in m_dataset.columns:
            st.warning("⚠️ Os dados avançados de formação e Field Tilt ainda não estão carregados. Clique em '🔄 Recarregar Dados' na barra lateral.")
            return

        # Análise de Formações: Filtro contextual de temporadas
        tab4_seasons = st.multiselect(
            "Filtrar Temporadas para a Amostra de Esquemas:",
            all_seasons,
            default=all_seasons,
            key="diag_uni_tab4_seasons"
        )

        form_df = m_dataset[
            (m_dataset["season"].isin(tab4_seasons)) &
            (m_dataset["palmeiras_formation"].notna()) & 
            (m_dataset["palmeiras_formation"] != "Desconhecida")
        ].copy()

        # Criar coluna de Família Tática (Linha de 4 vs Linha de 3/5)
        form_df["familia_tatica"] = form_df["palmeiras_formation"].apply(
            lambda f: "Linha de 3/5 Zagueiros" if str(f).startswith(("3-", "5-")) else "Linha de 4 Defensores"
        )

        # ---------------------------------------------------------------------
        # SEÇÃO 1: O DUELO DE SISTEMAS (LINHA DE 4 VS LINHA DE 3/5)
        # ---------------------------------------------------------------------
        st.markdown("##### 1. O Grande Duelo de Sistemas: Linha de 4 vs. Linha de 3/5")
        st.caption("Comparação agregada direta entre os dois modelos estruturais mais utilizados por Abel Ferreira.")

        fam_agg = form_df.groupby("familia_tatica").agg(
            partidas=("match_id", "count"),
            vitorias=("result", lambda s: (s == "Vitória").sum()),
            aproveitamento=("result", lambda s: ((s == "Vitória").sum() * 3 + (s == "Empate").sum()) / (len(s) * 3) * 100),
            xg_pro=("palmeiras_xg", "mean"),
            xg_contra=("opponent_xg", "mean"),
            field_tilt=("field_tilt", "mean"),
            toques_area=("palmeiras_touches_in_box", "mean"),
            cruzamentos=("palmeiras_crosses_attempted", "mean"),
            passes_profundidade=("palmeiras_through_balls", "mean"),
            posse=("palmeiras_possession", "mean")
        ).reset_index()
        fam_agg["saldo_xg"] = fam_agg["xg_pro"] - fam_agg["xg_contra"]

        c_fam1, c_fam2 = st.columns(2)

        for i, row in fam_agg.iterrows():
            with (c_fam1 if i == 0 else c_fam2):
                border_col = "#00FF87" if "Linha de 4" in row["familia_tatica"] else "#00BFFF"
                st.markdown(
                    f"""
                    <div style="border: 2px solid {border_col}; border-radius: 8px; padding: 14px; background: #18202C; margin-bottom: 15px;">
                        <h4 style="margin: 0 0 10px 0; color: {border_col};">{row['familia_tatica']}</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.92rem;">
                            <div><b>Amostra:</b> {row['partidas']} jogos</div>
                            <div><b>Aprov. Pontos:</b> {row['aproveitamento']:.1f}%</div>
                            <div><b>Field Tilt Médio:</b> {row['field_tilt']:.1f}%</div>
                            <div><b>Posse de Bola:</b> {row['posse']:.1f}%</div>
                            <div><b>xG Pró / Jogo:</b> {row['xg_pro']:.2f}</div>
                            <div><b>xG Contra / Jogo:</b> {row['xg_contra']:.2f}</div>
                            <div><b>Saldo xG:</b> <span style="color: {'#00FF87' if row['saldo_xg']>0 else '#FF4B4B'}">{row['saldo_xg']:+.2f}</span></div>
                            <div><b>Toques na Área:</b> {row['toques_area']:.1f} / jogo</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("---")

        # ---------------------------------------------------------------------
        # SEÇÃO 2: MATRIZ DE DOMINÂNCIA & PENETRAÇÃO POR ESQUEMA DETALHADO
        # ---------------------------------------------------------------------
        st.markdown("##### 2. Matriz de Dominância Tática por Formação Específica")
        st.caption("Mapeia onde cada esquema se posiciona: Field Tilt (%) no eixo X vs Saldo de xG no eixo Y. Tamanho da bolha = número de jogos.")

        # Manter esquemas com ao menos 3 jogos
        form_counts = form_df["palmeiras_formation"].value_counts()
        valid_formations = form_counts[form_counts >= 3].index.tolist()
        form_filtered = form_df[form_df["palmeiras_formation"].isin(valid_formations)].copy()

        if form_filtered.empty:
            st.info("Nenhuma formação com pelo menos 3 partidas no recorte selecionado.")
        else:
            form_agg = form_filtered.groupby("palmeiras_formation").agg(
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

            form_agg["vit_pct"] = (form_agg["vitorias"] / form_agg["partidas"] * 100).round(1)
            form_agg["saldo_xg"] = (form_agg["xg_pro"] - form_agg["xg_contra"]).round(2)
            form_agg["xg_pro"] = form_agg["xg_pro"].round(2)
            form_agg["xg_contra"] = form_agg["xg_contra"].round(2)
            form_agg["field_tilt"] = form_agg["field_tilt"].round(1)
            form_agg["toques_area"] = form_agg["toques_area"].round(1)
            form_agg["cruzamentos"] = form_agg["cruzamentos"].round(1)
            form_agg["posse"] = form_agg["posse"].round(1)

            c_sc1, c_sc2 = st.columns([1.1, 1.1])

            with c_sc1:
                st.markdown("###### Matriz: Field Tilt vs. Saldo de xG por Formação")
                fig_mat = px.scatter(
                    form_agg,
                    x="field_tilt",
                    y="saldo_xg",
                    size="partidas",
                    color="vit_pct",
                    text="palmeiras_formation",
                    hover_data={
                        "palmeiras_formation": True,
                        "partidas": True,
                        "field_tilt": ":.1f",
                        "saldo_xg": ":+.2f",
                        "vit_pct": ":.1f",
                        "toques_area": ":.1f"
                    },
                    color_continuous_scale="Viridis",
                    template="plotly_dark",
                    labels={
                        "field_tilt": "Field Tilt Médio (% Ocupação Terço Final)",
                        "saldo_xg": "Saldo Médio de xG (Pró - Contra)",
                        "vit_pct": "% Vitórias"
                    }
                )
                fig_mat.add_vline(x=50.0, line_dash="dash", line_color="#777777")
                fig_mat.add_hline(y=0.0, line_dash="dash", line_color="#777777")
                fig_mat.update_traces(textposition="top center")
                fig_mat.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_mat, use_container_width=True)

            with c_sc2:
                st.markdown("###### Como o Time Entra na Área: Cruzamentos vs. Passes em Profundidade")
                st.caption("Compara a preferência de penetração (bolas aéreas vs rupturas por baixo) por formação.")

                fig_pen = go.Figure()
                fig_pen.add_trace(go.Bar(
                    x=form_agg["palmeiras_formation"], y=form_agg["cruzamentos"],
                    name="Cruzamentos Tentados / Jogo",
                    marker_color="#FFA500",
                    text=form_agg["cruzamentos"].apply(lambda v: f"{v:.1f}"),
                    textposition="outside"
                ))
                fig_pen.add_trace(go.Bar(
                    x=form_agg["palmeiras_formation"], y=form_agg["through_balls"].round(1),
                    name="Passes em Profundidade / Jogo",
                    marker_color="#00FF87",
                    text=form_agg["through_balls"].apply(lambda v: f"{v:.1f}"),
                    textposition="outside"
                ))
                fig_pen.update_layout(
                    template="plotly_dark",
                    height=380,
                    barmode="group",
                    margin=dict(l=10, r=10, t=30, b=10),
                    yaxis_title="Média por Partida",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_pen, use_container_width=True)

            st.markdown("---")

            # Tabela Analítica Completa das Formações
            st.markdown("##### 3. Tabela Comparativa Detalhada por Esquema Tático")
            display_form = form_agg.rename(columns={
                "palmeiras_formation": "Formação",
                "partidas": "Jogos",
                "vit_pct": "Vitórias (%)",
                "xg_pro": "xG Pró / Jogo",
                "xg_contra": "xG Contra / Jogo",
                "saldo_xg": "Saldo xG",
                "field_tilt": "Field Tilt Médio (%)",
                "toques_area": "Toques na Área / Jogo",
                "cruzamentos": "Cruzamentos / Jogo",
                "posse": "Posse Média (%)"
            })
            st.dataframe(
                display_form.sort_values(by="Jogos", ascending=False),
                use_container_width=True,
                hide_index=True
            )

    # =========================================================================
    # GUIA METODOLÓGICO & FORMULÁRIO TÁTICO NO RODAPÉ
    # =========================================================================
    with st.expander("📖 Guia Metodológico & Formulações Matemáticas (Consulta Aprofundada)", expanded=False):
        st.markdown(r"""
        ### 🎯 Qual pergunta cada análise responde?
        1. **Decomposição Fatorial Waterfall:** Responde se o Palmeiras melhorou ou piorou por volume (mais chutes) ou por qualidade (melhor pontaria e seleção de jogadas).
           $$\\Delta xG_{90} = \\Delta V \\cdot \\bar{Q} + \\bar{V} \\cdot \\Delta Q$$
           *onde $V$ é o volume de finalizações por 90 minutos e $Q$ é o $xG$ médio por chute.*
        2. **Vetor de Deslocamento Tático:** Posiciona a equipe em 4 quadrantes ofensivos (Ataque de Elite, Clínico, Volume Forçado, Inoperante) e traça uma reta com seta indicando para qual perfil a equipe de Abel Ferreira migrou no tempo.
        3. **Identidade Espacial e Corredores:** Afunilamento no corredor central vs alargamento nas pontas, além da proporção de chutes dentro e fora da área.
        4. **Field Tilt (%):** Proporção de ações no terço ofensivo em relação ao adversário. Revela dominância territorial verdadeira, livre da armadilha de posse passiva na defesa.
        5. **Linha de 4 vs. Linha de 3/5:** Avalia se formações com 3 zagueiros geram solidez defensiva sem sacrificar o volume e a ocupação do terço final.
        """)
'''

with open("app/modules/mod6_tactical_diagnosis.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated mod6_tactical_diagnosis.py successfully!")
