"""
Módulo de visualização avançada de mapas de calor, densidade 2D e zonas táticas de finalização.
Resolve o problema de sobreposição e saturação visual quando há centenas de chutes.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.visualization.pitch_plotly import create_plotly_pitch_figure, COLOR_OUTCOME_MAP

def plot_density_shotmap(df_shots: pd.DataFrame, title: str = "Mapa de Densidade Espacial de Finalizações (KDE)") -> go.Figure:
    """
    Renderiza um mapa de contorno de densidade 2D (heatmap) sobre o campo FIFA.
    Mostra as zonas quentes de finalização sem a poluição de centenas de círculos sobrepostos.
    """
    fig = create_plotly_pitch_figure(half_pitch=True)
    
    if df_shots.empty:
        fig.update_layout(title=dict(text=f"{title} (Sem dados)", font=dict(color="white")))
        return fig

    shots = df_shots.copy()
    shots["pitch_x"] = 105.0 - (shots["x_pct"] * 1.05)
    shots["pitch_y"] = (shots["y_pct"] / 100.0) * 68.0

    # Adicionar contorno de densidade 2D (Histogram2dContour)
    fig.add_trace(go.Histogram2dContour(
        x=shots["pitch_x"],
        y=shots["pitch_y"],
        name="Densidade de Chutes",
        colorscale="Viridis",
        reversescale=False,
        showscale=False,
        ncontours=20,
        opacity=0.65,
        contours=dict(
            coloring="heatmap",
            showlines=False
        ),
        hoverinfo="skip"
    ))

    # Plotar apenas os Gols como marcadores luminosos de destaque
    goals = shots[shots["is_goal"] == True]
    if not goals.empty:
        hover_text = [
            f"⚽ <b>GOL! {row['player_name']}</b> ({row['minute']}')<br>"
            f"xG: <b>{row['xg']:.3f}</b> | Dist: {row['distance_meters']:.1f}m<br>"
            f"Situação: {row['situation']} | Placar: {row['score_palmeiras_before']}x{row['score_opponent_before']}"
            for _, row in goals.iterrows()
        ]
        fig.add_trace(go.Scatter(
            x=goals["pitch_x"],
            y=goals["pitch_y"],
            mode="markers",
            name="Gols Marcados",
            marker=dict(
                size=12,
                color="#00FF87",
                symbol="star",
                line=dict(color="white", width=1.5)
            ),
            text=hover_text,
            hoverinfo="text"
        ))

    total_s = len(shots)
    total_g = shots["is_goal"].sum()
    total_xg = shots["xg"].sum()
    subtitle = f"Volume: {total_s} finalizações | Gols: {total_g} | xG: {total_xg:.2f}"

    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b><br><span style='font-size:12px;color:#9bb0cf'>{subtitle}</span>",
            font=dict(color="white", size=15),
            x=0.05, y=0.96
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    return fig

def plot_tactical_zones_pitch(df_shots: pd.DataFrame, title: str = "Distribuição de xG por Zonas Táticas") -> go.Figure:
    """
    Divide a metade ofensiva em 5 zonas táticas:
    - Pequena Área (Faixa de Ouro)
    - Grande Área Central (Funil)
    - Flanco Esquerdo da Área
    - Flanco Direito da Área
    - Fora da Área (Longa Distância)
    """
    fig = create_plotly_pitch_figure(half_pitch=True)
    
    if df_shots.empty:
        return fig

    shots = df_shots.copy()
    total_shots = len(shots)
    total_xg = shots["xg"].sum()

    # Definir as coordenadas e métricas das zonas
    # 1. Pequena Área: [99.5, 105] x [24.84, 43.16]
    # 2. Grande Área Centro: [88.5, 99.5] x [24.84, 43.16]
    # 3. Flanco Direito da Área: [88.5, 105] x [43.16, 54.16]
    # 4. Flanco Esquerdo da Área: [88.5, 105] x [13.84, 24.84]
    # 5. Fora da Área: restante
    
    # Classificar zona específica para o mapa
    shots["pitch_x"] = 105.0 - (shots["x_pct"] * 1.05)
    shots["pitch_y"] = (shots["y_pct"] / 100.0) * 68.0

    def assign_tactical_zone(row):
        px, py = row["pitch_x"], row["pitch_y"]
        if px >= 99.5 and 24.84 <= py <= 43.16:
            return "Pequena Área"
        elif 88.5 <= px < 99.5 and 24.84 <= py <= 43.16:
            return "Grande Área (Centro)"
        elif px >= 88.5 and py > 43.16 and py <= 54.16:
            return "Área (Lado Direito)"
        elif px >= 88.5 and py >= 13.84 and py < 24.84:
            return "Área (Lado Esquerdo)"
        else:
            return "Fora da Área"

    shots["tactical_zone"] = shots.apply(assign_tactical_zone, axis=1)

    zone_stats = shots.groupby("tactical_zone").agg(
        chutes=("shot_id", "count"),
        xg_total=("xg", "sum"),
        gols=("is_goal", "sum")
    ).reset_index()

    zone_stats["pct_chutes"] = (zone_stats["chutes"] / total_shots * 100).round(1)
    zone_stats["pct_xg"] = (zone_stats["xg_total"] / total_xg * 100).round(1) if total_xg > 0 else 0
    zone_stats["xg_p_chute"] = (zone_stats["xg_total"] / zone_stats["chutes"]).round(3)
    zone_stats["conv_pct"] = (zone_stats["gols"] / zone_stats["chutes"] * 100).round(1)

    stats_dict = zone_stats.set_index("tactical_zone").to_dict(orient="index")

    # Desenhar retângulos das zonas com preenchimento colorido
    zones_config = [
        {
            "name": "Pequena Área",
            "x0": 99.5, "x1": 105.0, "y0": 24.84, "y1": 43.16,
            "color": "rgba(0, 255, 135, 0.25)",
            "center_x": 102.25, "center_y": 34.0
        },
        {
            "name": "Grande Área (Centro)",
            "x0": 88.5, "x1": 99.5, "y0": 24.84, "y1": 43.16,
            "color": "rgba(0, 191, 255, 0.22)",
            "center_x": 94.0, "center_y": 34.0
        },
        {
            "name": "Área (Lado Direito)",
            "x0": 88.5, "x1": 105.0, "y0": 43.16, "y1": 54.16,
            "color": "rgba(255, 165, 0, 0.20)",
            "center_x": 96.75, "center_y": 48.66
        },
        {
            "name": "Área (Lado Esquerdo)",
            "x0": 88.5, "x1": 105.0, "y0": 13.84, "y1": 24.84,
            "color": "rgba(255, 165, 0, 0.20)",
            "center_x": 96.75, "center_y": 19.34
        },
        {
            "name": "Fora da Área",
            "x0": 52.5, "x1": 88.5, "y0": 0.0, "y1": 68.0,
            "color": "rgba(255, 75, 75, 0.12)",
            "center_x": 70.5, "center_y": 34.0
        }
    ]

    for z in zones_config:
        fig.add_shape(
            type="rect",
            x0=z["x0"], y0=z["y0"], x1=z["x1"], y1=z["y1"],
            fillcolor=z["color"],
            line=dict(color="rgba(255,255,255,0.4)", width=1.5, dash="dot"),
            layer="below"
        )
        # Inserir anotação com métricas da zona
        z_data = stats_dict.get(z["name"], {"chutes": 0, "pct_chutes": 0, "pct_xg": 0, "xg_p_chute": 0, "gols": 0})
        label_text = (
            f"<b>{z['name']}</b><br>"
            f"Chutes: {z_data['chutes']} ({z_data['pct_chutes']}%)<br>"
            f"xG: {z_data['pct_xg']}% | Gols: {z_data['gols']}<br>"
            f"Qualidade: {z_data['xg_p_chute']:.2f} xG/ch"
        )
        fig.add_annotation(
            x=z["center_x"], y=z["center_y"],
            text=label_text,
            showarrow=False,
            font=dict(color="white", size=10),
            bgcolor="rgba(20, 26, 40, 0.85)",
            bordercolor="rgba(255,255,255,0.3)",
            borderwidth=1,
            borderpad=4
        )

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(color="white", size=15), x=0.05, y=0.96)
    )
    return fig
