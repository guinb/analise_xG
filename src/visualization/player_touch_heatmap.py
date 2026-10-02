"""
Visualização do Mapa de Calor Real de Toques de Jogador (Full Pitch 105m x 68m).
Renderiza o campo completo de futebol com as linhas regulamentares da FIFA
e a distribuição de densidade 2D de todos os toques na bola do atleta durante a partida.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any

def create_full_pitch_figure() -> go.Figure:
    """Desenha as linhas regulamentares do campo completo da FIFA (105m x 68m)."""
    fig = go.Figure()
    line_color = "rgba(255, 255, 255, 0.35)"
    grass_color = "#0e1117"

    # 1. Limite externo do campo
    fig.add_shape(
        type="rect", x0=0, y0=0, x1=105, y1=68,
        line=dict(color=line_color, width=2),
        fillcolor=grass_color, layer="below"
    )

    # 2. Linha de meio-campo
    fig.add_shape(
        type="line", x0=52.5, y0=0, x1=52.5, y1=68,
        line=dict(color=line_color, width=2), layer="below"
    )

    # 3. Círculo central (raio 9.15m em (52.5, 34))
    fig.add_shape(
        type="circle",
        x0=52.5 - 9.15, y0=34 - 9.15, x1=52.5 + 9.15, y1=34 + 9.15,
        line=dict(color=line_color, width=1.5), layer="below"
    )

    # 4. Grande Área Esquerda (Defesa/Ataque) [0, 16.5] x [13.84, 54.16]
    fig.add_shape(
        type="rect", x0=0, y0=13.84, x1=16.5, y1=54.16,
        line=dict(color=line_color, width=1.5), layer="below"
    )
    # Pequena Área Esquerda [0, 5.5] x [24.84, 43.16]
    fig.add_shape(
        type="rect", x0=0, y0=24.84, x1=5.5, y1=43.16,
        line=dict(color=line_color, width=1.5), layer="below"
    )

    # 5. Grande Área Direita [88.5, 105] x [13.84, 54.16]
    fig.add_shape(
        type="rect", x0=88.5, y0=13.84, x1=105, y1=54.16,
        line=dict(color=line_color, width=1.5), layer="below"
    )
    # Pequena Área Direita [99.5, 105] x [24.84, 43.16]
    fig.add_shape(
        type="rect", x0=99.5, y0=24.84, x1=105, y1=43.16,
        line=dict(color=line_color, width=1.5), layer="below"
    )

    # Traves nos dois lados
    fig.add_shape(type="rect", x0=-2, y0=30.34, x1=0, y1=37.66, line=dict(color="white", width=2.5), layer="below")
    fig.add_shape(type="rect", x0=105, y0=30.34, x1=107, y1=37.66, line=dict(color="white", width=2.5), layer="below")

    # Eixos
    fig.update_xaxes(range=[-3, 108], showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(range=[-3, 71], showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1)

    fig.update_layout(
        plot_bgcolor=grass_color,
        paper_bgcolor=grass_color,
        margin=dict(l=10, r=10, t=35, b=10)
    )
    return fig

def plot_player_touch_heatmap(
    heatmap_points: List[Dict[str, Any]],
    player_name: str,
    match_title: str,
    direction_right: bool = True
) -> go.Figure:
    fig = create_full_pitch_figure()

    if not heatmap_points:
        fig.update_layout(title=dict(text=f"Heatmap: {player_name} (Sem dados de toques)", font=dict(color="white")))
        return fig

    df_pts = pd.DataFrame(heatmap_points)
    if "x" not in df_pts.columns or "y" not in df_pts.columns:
        return fig

    # No SofaScore, x e y estão em porcentagem (0 a 100)
    # Converter para metros no campo 105m x 68m
    if direction_right:
        pitch_x = (df_pts["x"] / 100.0) * 105.0
        pitch_y = (df_pts["y"] / 100.0) * 68.0
    else:
        # Inverter para padronizar ataque para a direita
        pitch_x = 105.0 - ((df_pts["x"] / 100.0) * 105.0)
        pitch_y = 68.0 - ((df_pts["y"] / 100.0) * 68.0)

    # 1. Adicionar contorno de densidade 2D (Heatmap KDE)
    fig.add_trace(go.Histogram2dContour(
        x=pitch_x,
        y=pitch_y,
        name="Densidade de Toques",
        colorscale="Hot",
        reversescale=True,
        showscale=False,
        ncontours=25,
        opacity=0.75,
        contours=dict(coloring="heatmap", showlines=False),
        hoverinfo="skip"
    ))

    # 2. Indicador de seta de ataque no topo
    fig.add_annotation(
        x=52.5, y=69.5,
        text="Direção do Ataque ➔",
        showarrow=False,
        font=dict(color="#00FF87", size=11, family="sans-serif")
    )

    total_touches = len(df_pts)
    touches_attacking_half = (pitch_x >= 52.5).sum()
    pct_att = (touches_attacking_half / total_touches * 100) if total_touches > 0 else 0

    subtitle = f"Partida: {match_title} | Total de Toques: {total_touches} | No Campo de Ataque: {pct_att:.0f}%"

    fig.update_layout(
        title=dict(
            text=f"<b>Heatmap Real de Toques: {player_name}</b><br><span style='font-size:12px;color:#9bb0cf'>{subtitle}</span>",
            font=dict(color="white", size=15),
            x=0.05, y=0.96
        )
    )

    return fig
