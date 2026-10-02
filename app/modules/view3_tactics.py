# -*- coding: utf-8 -*-
"""
View 3: O Modelo de Abel Ferreira: Formações Táticas & Campo.
Responde como a estrutura tática molda o domínio territorial (Field Tilt) e o balanço xG:
- Explicação Front-and-Center de Field Tilt
- Duelo Estrutural: Linha de 4 Defensores vs Linha de 3/5 Zagueiros
- Cards de Perfis Táticos (Melhor Ataque, Defesa, Saldo e Field Tilt)
- Balanço de xG e Gols por Esquema
- Prancheta Tática Compacta em Plotly (440px) com conferência de escalações reais do SofaScore
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from pathlib import Path

# Mapeamento tático de posições para as principais formações de Abel Ferreira
FORMATION_SLOTS = {
    "4-2-3-1": [
        ("GOL", "Goleiro", 50, 8),
        ("LE", "Lateral Esquerdo", 14, 24), ("ZAE", "Zagueiro Esquerdo", 38, 22), ("ZAD", "Zagueiro Direito", 62, 22), ("LD", "Lateral Direito", 86, 24),
        ("VOL", "Primeiro Volante", 38, 42), ("VOL", "Segundo Volante", 62, 42),
        ("ME", "Meia Esquerda", 16, 62), ("MEI", "Meia Central", 50, 64), ("MD", "Meia Direita", 84, 62),
        ("CA", "Centroavante", 50, 84)
    ],
    "4-2-2-2": [
        ("GOL", "Goleiro", 50, 8),
        ("LE", "Lateral Esquerdo", 14, 24), ("ZAE", "Zagueiro Esquerdo", 38, 22), ("ZAD", "Zagueiro Direito", 62, 22), ("LD", "Lateral Direito", 86, 24),
        ("VOL", "Volante", 38, 42), ("VOL", "Volante", 62, 42),
        ("MEI", "Meia Ofensivo", 34, 62), ("MEI", "Meia Ofensivo", 66, 62),
        ("CA", "Centroavante", 36, 82), ("ATA", "Segundo Atacante", 64, 82)
    ],
    "3-4-2-1": [
        ("GOL", "Goleiro", 50, 8),
        ("ZAE", "Zagueiro Esquerdo", 26, 22), ("ZAC", "Zagueiro Central", 50, 20), ("ZAD", "Zagueiro Direito", 74, 22),
        ("ALA E", "Ala Esquerdo", 12, 44), ("VOL", "Volante", 38, 42), ("VOL", "Volante", 62, 42), ("ALA D", "Ala Direito", 88, 44),
        ("MEI", "Meia Atacante", 34, 64), ("MEI", "Meia Atacante", 66, 64),
        ("CA", "Centroavante", 50, 84)
    ],
    "3-5-2": [
        ("GOL", "Goleiro", 50, 8),
        ("ZAE", "Zagueiro Esquerdo", 26, 22), ("ZAC", "Zagueiro Central", 50, 20), ("ZAD", "Zagueiro Direito", 74, 22),
        ("ALA E", "Ala Esquerdo", 12, 44), ("VOL", "Volante", 38, 42), ("MEI", "Meia Central", 50, 56), ("VOL", "Volante", 62, 42), ("ALA D", "Ala Direito", 88, 44),
        ("CA", "Centroavante", 36, 80), ("ATA", "Segundo Atacante", 64, 80)
    ],
    "4-3-3": [
        ("GOL", "Goleiro", 50, 8),
        ("LE", "Lateral Esquerdo", 14, 24), ("ZAE", "Zagueiro Esquerdo", 38, 22), ("ZAD", "Zagueiro Direito", 62, 22), ("LD", "Lateral Direito", 86, 24),
        ("VOL", "Primeiro Volante", 50, 42), ("MC", "Meia Central", 34, 54), ("MC", "Meia Central", 66, 54),
        ("PE", "Ponta Esquerda", 16, 76), ("CA", "Centroavante", 50, 84), ("PD", "Ponta Direita", 84, 76)
    ],
    "4-4-2": [
        ("GOL", "Goleiro", 50, 8),
        ("LE", "Lateral Esquerdo", 14, 24), ("ZAE", "Zagueiro Esquerdo", 38, 22), ("ZAD", "Zagueiro Direito", 62, 22), ("LD", "Lateral Direito", 86, 24),
        ("ME", "Meia Esquerda", 16, 48), ("VOL", "Volante", 38, 46), ("VOL", "Volante", 62, 46), ("MD", "Meia Direita", 84, 48),
        ("CA", "Centroavante", 36, 80), ("ATA", "Segundo Atacante", 64, 80)
    ],
    "3-4-1-2": [
        ("GOL", "Goleiro", 50, 8),
        ("ZAE", "Zagueiro Esquerdo", 26, 22), ("ZAC", "Zagueiro Central", 50, 20), ("ZAD", "Zagueiro Direito", 74, 22),
        ("ALA E", "Ala Esquerdo", 12, 44), ("VOL", "Primeiro Volante", 38, 42), ("VOL", "Segundo Volante", 62, 42), ("ALA D", "Ala Direito", 88, 44),
        ("MEI", "Meia Armador", 50, 62),
        ("CA", "Centroavante", 36, 82), ("ATA", "Segundo Atacante", 64, 82)
    ],
    "3-4-3": [
        ("GOL", "Goleiro", 50, 8),
        ("ZAE", "Zagueiro Esquerdo", 26, 22), ("ZAC", "Zagueiro Central", 50, 20), ("ZAD", "Zagueiro Direito", 74, 22),
        ("ALA E", "Ala Esquerdo", 12, 44), ("VOL", "Volante", 38, 42), ("VOL", "Volante", 62, 42), ("ALA D", "Ala Direito", 88, 44),
        ("PE", "Ponta Esquerda", 18, 76), ("CA", "Centroavante", 50, 84), ("PD", "Ponta Direita", 82, 76)
    ]
}

def get_formation_slots(formation: str):
    form_str = str(formation).strip()
    if form_str in FORMATION_SLOTS:
        return FORMATION_SLOTS[form_str]
    try:
        lines = [int(x) for x in form_str.split('-')]
    except Exception:
        lines = [4, 4, 2]
    slots = [("GOL", "Goleiro", 50, 8)]
    n_lines = len(lines)
    y_positions = [22 + i * (62 / max(1, n_lines - 1)) for i in range(n_lines)]
    for idx, (count, y) in enumerate(zip(lines, y_positions)):
        if count == 1:
            xs = [50]
        elif count == 2:
            xs = [36, 64]
        elif count == 3:
            xs = [24, 50, 76] if idx == 0 else [18, 50, 82]
        elif count == 4:
            xs = [14, 38, 62, 86]
        elif count == 5:
            xs = [12, 31, 50, 69, 88]
        else:
            xs = [15 + j * (70 / max(1, count - 1)) for j in range(count)]
        for j, x in enumerate(xs):
            tag = "ZAG" if idx == 0 else ("VOL" if idx == 1 and n_lines > 3 else ("MEI" if idx < n_lines - 1 else "ATA"))
            slots.append((tag, f"Linha {idx+1}", round(x, 1), round(y, 1)))
    return slots[:11]

def draw_compact_plotly_pitch(formation, players_list=None):
    """Gera visualização de campo compacta e interativa usando Plotly (440px de altura)."""
    fig = go.Figure()
    # Desenho das linhas do gramado - IMPORTANTE: layer='below' para não cobrir os atletas
    fig.add_shape(type="rect", x0=2, y0=2, x1=98, y1=98, line=dict(color="#4A7552", width=1.5), fillcolor="#122416", layer="below")
    fig.add_shape(type="line", x0=2, y0=50, x1=98, y1=50, line=dict(color="#4A7552", width=1.2), layer="below")
    fig.add_shape(type="circle", x0=36, y0=36, x1=64, y1=64, line=dict(color="#4A7552", width=1.2), layer="below")
    fig.add_shape(type="circle", x0=49, y0=49, x1=51, y1=51, fillcolor="#4A7552", line_color="#4A7552", layer="below")

    # Grandes e pequenas áreas (lado inferior - defesa)
    fig.add_shape(type="rect", x0=20, y0=2, x1=80, y1=19, line=dict(color="#4A7552", width=1.2), layer="below")
    fig.add_shape(type="rect", x0=34, y0=2, x1=66, y1=7, line=dict(color="#4A7552", width=1.2), layer="below")
    fig.add_shape(type="circle", x0=49.2, y0=12.5, x1=50.8, y1=14.1, fillcolor="#4A7552", line_color="#4A7552", layer="below")

    # Grandes e pequenas áreas (lado superior - ataque)
    fig.add_shape(type="rect", x0=20, y0=81, x1=80, y1=98, line=dict(color="#4A7552", width=1.2), layer="below")
    fig.add_shape(type="rect", x0=34, y0=93, x1=66, y1=98, line=dict(color="#4A7552", width=1.2), layer="below")
    fig.add_shape(type="circle", x0=49.2, y0=85.9, x1=50.8, y1=87.5, fillcolor="#4A7552", line_color="#4A7552", layer="below")

    slots = get_formation_slots(formation)
    xs = [s[2] for s in slots]
    ys = [s[3] for s in slots]

    if players_list and len(players_list) >= 11:
        # Modo Real: Exibe o número na camisa e o nome + posição
        inner_texts = [str(p.get("shirtNumber", "")) for p in players_list[:11]]
        captions = [f"<b>{p.get('name', '').split()[-1]}</b><br><span style='color:#00FF87;'>[{slots[i][0]}]</span>" for i, p in enumerate(players_list[:11])]
        hover_texts = [f"#{p.get('shirtNumber', '')} {p.get('name', '')}<br>Posição em Campo: <b>{slots[i][0]}</b> ({slots[i][1]})" for i, p in enumerate(players_list[:11])]
    else:
        # Modo Gabarito Teórico: Exibe a sigla da posição dentro do círculo e o nome da posição acima
        inner_texts = [s[0] for s in slots]
        captions = [f"<b>{s[0]}</b><br><span style='color:#cbd5e1; font-size:9px;'>{s[1]}</span>" for s in slots]
        hover_texts = [f"Posição Tática: <b>{s[0]}</b> - {s[1]}" for s in slots]

    # 1. Traço dos círculos com o texto interno
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="markers+text",
        marker=dict(size=28, color="#00FF87", line=dict(color="#0A1E11", width=2)),
        text=inner_texts,
        textposition="middle center",
        textfont=dict(color="#0A1E11", size=10, family="Arial Black"),
        hovertext=hover_texts,
        hoverinfo="text",
        name="Jogadores"
    ))

    # 2. Traço das legendas descritivas (nomes / posições) logo acima dos círculos
    caption_ys = [min(96, y + 5.2) for y in ys]
    fig.add_trace(go.Scatter(
        x=xs, y=caption_ys,
        mode="text",
        text=captions,
        textposition="top center",
        textfont=dict(color="#FFFFFF", size=9.5),
        hoverinfo="skip",
        showlegend=False
    ))

    fig.update_layout(
        template="plotly_dark",
        height=450,
        margin=dict(l=5, r=5, t=5, b=5),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 100], fixedrange=True),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-2, 104], fixedrange=True),
        showlegend=False
    )
    return fig

def render_tactics_view(df_matches_full: pd.DataFrame):
    st.markdown("### 🛡️ O Modelo de Abel: Formações & Prancheta Tática")
    st.caption("Investigação do impacto dos esquemas táticos de Abel Ferreira na dominância territorial, no perigo criado e na solidez defensiva.")

    if df_matches_full.empty:
        st.warning("Dados de partidas não disponíveis.")
        return

    # Banner Front-and-Center de Field Tilt
    st.markdown(
        """
        <div style="background-color: #1A2332; border: 1px solid #2A3B50; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;">
            <h4 style="color: #00FF87; margin-top: 0; margin-bottom: 8px;">📖 O que é Field Tilt (% de Domínio Territorial)?</h4>
            <p style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.5; margin-bottom: 10px;">
                O <b>Field Tilt</b> mede a porcentagem de ações e entradas no <b>terço ofensivo</b> do campo em relação ao rival:
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

    form_df = df_matches_full[
        (df_matches_full["palmeiras_formation"].notna()) & 
        (df_matches_full["palmeiras_formation"] != "Desconhecida")
    ].copy()

    if form_df.empty:
        st.warning("Dados de formações táticas não encontrados.")
        return

    form_df["familia_tatica"] = form_df["palmeiras_formation"].apply(
        lambda f: "Linha de 3/5 Zagueiros" if str(f).startswith(("3-", "5-")) else "Linha de 4 Defensores"
    )

    # -------------------------------------------------------------------------
    # 1. DUELO ESTRUTURAL: LINHA DE 4 VS LINHA DE 3/5
    # -------------------------------------------------------------------------
    st.markdown("#### 1. Duelo Estrutural: Linha de 4 Defensores vs. Linha de 3/5 Zagueiros")
    st.caption("Comparação agregada entre os dois grandes blocos defensivos de Abel Ferreira.")

    fam_agg = form_df.groupby("familia_tatica").agg(
        partidas=("match_id", "count"),
        vitorias=("result", lambda s: (s == "Vitória").sum()),
        aproveitamento=("result", lambda s: ((s == "Vitória").sum() * 3 + (s == "Empate").sum()) / (len(s) * 3) * 100),
        xg_pro=("palmeiras_xg", "mean"),
        xg_contra=("opponent_xg", "mean"),
        gols_pro=("palmeiras_goals", "mean"),
        gols_contra=("opponent_goals", "mean"),
        field_tilt=("field_tilt", "mean"),
        toques_area=("palmeiras_touches_in_box", "mean"),
        posse=("palmeiras_possession", "mean")
    ).reset_index()
    fam_agg["saldo_xg"] = fam_agg["xg_pro"] - fam_agg["xg_contra"]
    fam_agg["saldo_gols"] = fam_agg["gols_pro"] - fam_agg["gols_contra"]

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

    # -------------------------------------------------------------------------
    # 2. CARDS DE PERFIL TÁTICO
    # -------------------------------------------------------------------------
    form_counts = form_df["palmeiras_formation"].value_counts()
    valid_formations = form_counts[form_counts >= 3].index.tolist()
    # Separate threshold: only formations with ≥ 8 games qualify for "best" highlights
    highlight_formations = form_counts[form_counts >= 8].index.tolist()
    form_filtered = form_df[form_df["palmeiras_formation"].isin(valid_formations)].copy()
    form_highlight = form_df[form_df["palmeiras_formation"].isin(highlight_formations)].copy() if highlight_formations else form_df[form_df["palmeiras_formation"].isin(valid_formations)].copy()

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

    # Aggregated stats for highlight formations only
    f_highlight_agg = form_highlight.groupby("palmeiras_formation").agg(
        partidas=("match_id", "count"),
        aproveitamento=("result", lambda s: ((s == "Vitória").sum() * 3 + (s == "Empate").sum()) / (len(s) * 3) * 100),
        xg_pro=("palmeiras_xg", "mean"),
        xg_contra=("opponent_xg", "mean"),
        field_tilt=("field_tilt", "mean"),
    ).reset_index()
    f_highlight_agg["saldo_xg"] = (f_highlight_agg["xg_pro"] - f_highlight_agg["xg_contra"]).round(2)

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

    # Use highlight_agg for "best" metrics to avoid small-sample distortion
    _fa = f_highlight_agg if not f_highlight_agg.empty else f_agg
    best_def = _fa.sort_values(by="xg_contra", ascending=True).iloc[0]
    best_att = _fa.sort_values(by="xg_pro", ascending=False).iloc[0]
    best_tilt = _fa.sort_values(by="field_tilt", ascending=False).iloc[0]
    best_balance = _fa.sort_values(by="saldo_xg", ascending=False).iloc[0]

    st.markdown("#### 2. Destaques: Qual Formação Entrega Cada Vantagem?")
    _min_note = f"(apenas formações com ≥ 8 jogos — base estatisticamente confiável)" if highlight_formations else "(amostra reduzida disponível)"
    st.caption(f"Identificação dos esquemas mais eficientes em cada aspecto do jogo. {_min_note}")

    c_p1, c_p2, c_p3, c_p4 = st.columns(4)
    c_p1.metric("🛡️ Melhor Defesa", best_def["palmeiras_formation"], f"{best_def['xg_contra']:.2f} xG sofrido/j ({int(best_def['partidas'])} jogos)")
    c_p2.metric("⚔️ Melhor Ataque", best_att["palmeiras_formation"], f"{best_att['xg_pro']:.2f} xG pró/j ({int(best_att['partidas'])} jogos)")
    c_p3.metric("🏟️ Maior Domínio Territorial", best_tilt["palmeiras_formation"], f"{best_tilt['field_tilt']:.1f}% Field Tilt ({int(best_tilt['partidas'])} jogos)")
    c_p4.metric("⚖️ Maior Saldo Estrutural", best_balance["palmeiras_formation"], f"{best_balance['saldo_xg']:+.2f} Saldo xG/j ({int(best_balance['partidas'])} jogos)")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. BALANÇO DE xG E GOLS POR ESTRUTURA (LINHA DE 4 VS LINHA DE 3/5)
    # -------------------------------------------------------------------------
    st.markdown("#### 3. Balanço Ofensivo vs. Defensivo: Linha de 4 vs. Linha de 3/5 Zagueiros")
    st.caption("Comparação direta do volume ofensivo e defensivo entre os dois grandes blocos táticos de Abel Ferreira.")

    c_fg1, c_fg2 = st.columns(2)
    with c_fg1:
        st.markdown("##### Gols Esperados por Jogo (xG)")
        fig_fx = go.Figure()
        fig_fx.add_trace(go.Bar(
            x=fam_agg["familia_tatica"], y=fam_agg["xg_pro"],
            name="xG Pró / Jogo (Criação)", marker_color="#00FF87",
            text=[f"{v:.2f}" for v in fam_agg["xg_pro"]], textposition="outside"
        ))
        fig_fx.add_trace(go.Bar(
            x=fam_agg["familia_tatica"], y=fam_agg["xg_contra"],
            name="xG Sofrido / Jogo (Perigo)", marker_color="#FF4B4B",
            text=[f"{v:.2f}" for v in fam_agg["xg_contra"]], textposition="outside"
        ))
        fig_fx.update_layout(
            template="plotly_dark", height=320, barmode="group",
            margin=dict(l=10, r=10, t=25, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_fx, use_container_width=True)

    with c_fg2:
        st.markdown("##### Gols Reais por Jogo (Rede)")
        fig_fg = go.Figure()
        fig_fg.add_trace(go.Bar(
            x=fam_agg["familia_tatica"], y=fam_agg["gols_pro"],
            name="Gols Marcados / Jogo", marker_color="#00BFFF",
            text=[f"{v:.2f}" for v in fam_agg["gols_pro"]], textposition="outside"
        ))
        fig_fg.add_trace(go.Bar(
            x=fam_agg["familia_tatica"], y=fam_agg["gols_contra"],
            name="Gols Sofridos / Jogo", marker_color="#FFA500",
            text=[f"{v:.2f}" for v in fam_agg["gols_contra"]], textposition="outside"
        ))
        fig_fg.update_layout(
            template="plotly_dark", height=320, barmode="group",
            margin=dict(l=10, r=10, t=25, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_fg, use_container_width=True)

    # Tabela Completa Formatada
    st.markdown("##### 📋 Tabela Comparativa Detalhada por Esquema Específico")
    st.caption("Detalhamento completo de cada formação com amostra mínima de 3 jogos. ⚠️ = amostra pequena (< 8 jogos) — interpretar com cautela.")
    # Add small sample badge
    f_agg_disp = f_agg.copy()
    f_agg_disp["Confiança"] = f_agg_disp["partidas"].apply(lambda n: "✅ Confiável" if n >= 8 else "⚠️ Amostra Pequena")
    disp_form = f_agg_disp.rename(columns={
        "palmeiras_formation": "Formação",
        "partidas": "Jogos",
        "vitorias": "Vitórias",
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
    # Reorder so Confiança appears after Jogos
    cols_order = ["Formação", "Jogos", "Vitórias", "Confiança", "Aprov. (%)", "xG Pró/J", "xG Contra/J", "Saldo xG", "Gols Pró/J", "Gols Contra/J", "Saldo Gols", "Field Tilt (%)", "Toques Área/J", "Cruzamentos/J", "Passes Prof./J", "Posse (%)"]
    disp_form = disp_form[[c for c in cols_order if c in disp_form.columns]]
    st.dataframe(disp_form.sort_values(by="Jogos", ascending=False), use_container_width=True, hide_index=True)

    st.markdown("---")

    # =========================================================================
    # NOVA SEÇÃO: SCATTER FIELD TILT vs xGD
    # =========================================================================
    st.markdown("#### 📡 Field Tilt vs Saldo de xG: Domínio Territorial Gera Criação?")
    st.caption(
        "Cada ponto representa uma formação. Eixo X = Field Tilt médio (domínio no terço adversário). "
        "Eixo Y = Saldo xG/jogo (xG criado − xG sofrido). Tamanho = amostra de jogos. Cor = aproveitamento."
    )

    if not f_agg.empty and "field_tilt" in f_agg.columns and "saldo_xg" in f_agg.columns:
        _scatter_df = f_agg[f_agg["partidas"] >= 3].copy()
        if not _scatter_df.empty:
            _fig_scatter = go.Figure()
            _fig_scatter.add_hline(y=0, line_color="#555555", line_dash="dot", line_width=1)
            _fig_scatter.add_vline(x=_scatter_df["field_tilt"].mean(), line_color="#555555", line_dash="dot", line_width=1)

            _color_vals = _scatter_df["aproveitamento"].values
            _cmin, _cmax = _color_vals.min(), _color_vals.max()

            _fig_scatter.add_trace(go.Scatter(
                x=_scatter_df["field_tilt"],
                y=_scatter_df["saldo_xg"],
                mode="markers+text",
                text=_scatter_df["palmeiras_formation"],
                textposition="top center",
                marker=dict(
                    size=np.clip(_scatter_df["partidas"] * 2.5, 14, 40),
                    color=_scatter_df["aproveitamento"],
                    colorscale=[[0, "#FF4B4B"], [0.5, "#F59E0B"], [1, "#00FF87"]],
                    cmin=_cmin, cmax=_cmax,
                    showscale=True,
                    colorbar=dict(title="Aproveit. (%)", thickness=14, len=0.7),
                    line=dict(color="#0e1117", width=1)
                ),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Field Tilt: %{x:.1f}%<br>"
                    "Saldo xG/j: %{y:+.2f}<br>"
                    f"Jogos: " + _scatter_df["partidas"].astype(str) +
                    f" | Aproveit: " + _scatter_df["aproveitamento"].round(1).astype(str) + "%"
                    "<extra></extra>"
                )
            ))

            _fig_scatter.update_layout(
                template="plotly_dark", height=420,
                margin=dict(l=10, r=10, t=20, b=30),
                xaxis=dict(title="Field Tilt Médio (% de ações no terço adversário)"),
                yaxis=dict(title="Saldo xG/jogo (xG criado − xG sofrido)", zeroline=False),
                annotations=[
                    dict(x=_scatter_df["field_tilt"].mean(), y=_scatter_df["saldo_xg"].max(),
                         text="← Abaixo da média | Acima da média →",
                         showarrow=False, font=dict(color="#555555", size=10), xanchor="center")
                ]
            )
            st.plotly_chart(_fig_scatter, use_container_width=True)

            # Correlação
            _corr = _scatter_df[["field_tilt", "saldo_xg"]].corr().iloc[0, 1]
            _corr_color = "#00FF87" if _corr > 0.3 else ("#FF4B4B" if _corr < -0.1 else "#F59E0B")
            st.markdown(
                f"<div style='background:#1a2234; border-left:3px solid {_corr_color}; border-radius:4px; padding:10px 16px; font-size:0.85rem; color:#E2E8F0;'>"
                f"📊 <b>Correlação Field Tilt × Saldo xG: {_corr:+.2f}</b> — "
                f"{'Correlação positiva moderada/forte: dominar territorialmente tende a gerar mais xGD.' if _corr > 0.3 else ('Correlação fraca ou negativa: Field Tilt elevado não garante superioridade xG — outros fatores são mais determinantes.' if _corr < 0.3 else 'Correlação neutra.')}"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.info("Amostra insuficiente para gerar o scatter de formações.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 4. PRANCHETA TÁTICA COMPACTA & VERIFICADOR DE JOGOS REAIS
    # -------------------------------------------------------------------------
    st.markdown("#### 🏟️ 4. Prancheta Tática & Verificador de Escalações em Campo")
    st.caption("Visualizador compacto (440px) e ultrarrápido para conferir a escalação de qualquer partida do histórico.")

    all_valid_forms = valid_formations if not form_filtered.empty else ["4-2-3-1", "3-4-2-1", "3-5-2", "4-4-2", "4-3-3", "4-2-2-2"]

    c_pf1, c_pf2 = st.columns([1.1, 1.9])
    with c_pf1:
        board_mode = st.radio(
            "Modo de Exibição da Prancheta:",
            ["🔍 Conferir Jogo Real no Campo", "📐 Gabarito Tático Teórico"],
            key="t3_board_mode"
        )

        real_players = None
        match_info = None
        sel_form = "4-2-3-1"

        if board_mode == "📐 Gabarito Tático Teórico":
            sel_form = st.selectbox("Selecione a Formação Tática:", all_valid_forms, key="t3_sel_form_theo")
            st.caption(f"Visualizando gabarito posicional teórico para o esquema **{sel_form}** com papéis táticos em campo.")

        else: # Conferir Jogo Real no Campo
            filter_mode = st.selectbox(
                "Filtrar Partidas por Formação:",
                ["Todas as Partidas (Mais Recentes Primeiro)"] + [f"Apenas {f}" for f in all_valid_forms],
                key="t3_filter_form"
            )

            if filter_mode == "Todas as Partidas (Mais Recentes Primeiro)":
                cand_matches = form_df.sort_values(by="date", ascending=False)
            else:
                f_target = filter_mode.replace("Apenas ", "")
                cand_matches = form_df[form_df["palmeiras_formation"] == f_target].sort_values(by="date", ascending=False)

            if not cand_matches.empty:
                match_opts = {}
                for _, r in cand_matches.iterrows():
                    key_str = f"{r['date']} - {r['tournament']}: {r['home_team']} {r['home_score']}x{r['away_score']} {r['away_team']} (Esquema: {r['palmeiras_formation']})"
                    match_opts[key_str] = r

                chosen_match_label = st.selectbox(
                    f"Escolha a partida ({len(match_opts)} disponíveis):",
                    list(match_opts.keys()),
                    key="t3_match_picker"
                )
                chosen_row = match_opts[chosen_match_label]
                match_info = chosen_row
                sel_form = chosen_row["palmeiras_formation"]

                RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
                json_path = RAW_DIR / str(chosen_row['season']) / f"event_{chosen_row['match_id']}_lineups.json"
                if json_path.exists():
                    try:
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
                    except Exception as e:
                        st.warning(f"Erro ao carregar escalação: {e}")

        if match_info is not None:
            st.markdown(
                f"""
                <div style="background-color: #1a2234; border: 1px solid #2d3a56; border-radius: 8px; padding: 12px; margin-top: 10px; margin-bottom: 10px;">
                    <span style="color:#00FF87; font-weight:bold;">Conferência de Jogo Real:</span><br>
                    🏆 <b>{match_info['tournament']}</b> | 📅 {match_info['date']}<br>
                    ⚽ Placar: <b>{match_info['palmeiras_score']} x {match_info['opponent_score']}</b> vs {match_info['opponent_name']}<br>
                    📋 Formação Detectada: <b style="color:#38BDF8;">{sel_form}</b><br>
                    📊 Posse: <b>{match_info['palmeiras_possession']:.1f}%</b> | Field Tilt: <b>{match_info['field_tilt']:.1f}%</b>
                </div>
                """,
                unsafe_allow_html=True
            )
            if real_players:
                st.caption("Titulares em Campo: " + ", ".join([f"{p['name']} (#{p['shirtNumber']})" for p in real_players]))

    with c_pf2:
        fig_pitch = draw_compact_plotly_pitch(sel_form, real_players)
        st.plotly_chart(fig_pitch, use_container_width=True)
