"""
Visualização interativa de campo de futebol e finalizações usando Plotly.
Converte coordenadas percentuais para metros (FIFA 105m x 68m) com ataque em direção ao gol direito (X = 105m).
Inclui linhas regulamentares da grande área, pequena área, marca do pênalti, meia-lua e traves.
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np

COLOR_OUTCOME_MAP = {
    "Gol": "#00FF87",         # Verde brilhante
    "Defesa": "#00BFFF",      # Azul elétrico
    "Para Fora": "#FF4B4B",    # Vermelho
    "Bloqueado": "#FFA500",   # Laranja
    "Trave": "#FFD700",       # Dourado
    "Outro": "#A0A0A0"        # Cinza
}

def create_plotly_pitch_figure(half_pitch: bool = True) -> go.Figure:
    """Desenha as linhas táticas regulamentares do campo no Plotly."""
    fig = go.Figure()
    
    line_color = "rgba(255, 255, 255, 0.35)"
    grass_color = "#0e1117"  # Dark mode analítico
    
    x_min = 52.5 if half_pitch else 0.0
    x_max = 105.0
    y_min = 0.0
    y_max = 68.0

    # Retângulo principal do campo / meio-campo
    fig.add_shape(
        type="rect",
        x0=x_min, y0=y_min, x1=x_max, y1=y_max,
        line=dict(color=line_color, width=2),
        fillcolor=grass_color,
        layer="below"
    )

    # Linha de meio-campo (se meio campo ou campo inteiro)
    fig.add_shape(
        type="line",
        x0=52.5, y0=0, x1=52.5, y1=68,
        line=dict(color=line_color, width=2),
        layer="below"
    )

    # Grande Área (Penalty Box) atacante (X: 88.5 a 105, Y: 13.84 a 54.16)
    fig.add_shape(
        type="rect",
        x0=88.5, y0=13.84, x1=105.0, y1=54.16,
        line=dict(color=line_color, width=1.5),
        layer="below"
    )

    # Pequena Área (Six-Yard Box) atacante (X: 99.5 a 105, Y: 24.84 a 43.16)
    fig.add_shape(
        type="rect",
        x0=99.5, y0=24.84, x1=105.0, y1=43.16,
        line=dict(color=line_color, width=1.5),
        layer="below"
    )

    # Marca do Pênalti atacante (X: 94.0, Y: 34.0)
    fig.add_shape(
        type="circle",
        x0=93.7, y0=33.7, x1=94.3, y1=34.3,
        fillcolor=line_color,
        line=dict(color=line_color),
        layer="below"
    )

    # Traves do Gol (X: 105.0 a 107.0, Y: 30.34 a 37.66)
    fig.add_shape(
        type="rect",
        x0=105.0, y0=30.34, x1=107.0, y1=37.66,
        line=dict(color="#FFFFFF", width=3),
        layer="below"
    )

    # Meia-lua da grande área (arco do raio de 9.15m a partir da marca do pênalti)
    theta = np.linspace(np.pi * 0.70, np.pi * 1.30, 30)
    arc_x = 94.0 - 9.15 * np.cos(theta - np.pi)
    arc_y = 34.0 + 9.15 * np.sin(theta - np.pi)
    fig.add_trace(go.Scatter(
        x=arc_x, y=arc_y, mode="lines",
        line=dict(color=line_color, width=1.5),
        hoverinfo="skip", showlegend=False
    ))

    # Configuração dos eixos
    fig.update_xaxes(
        range=[x_min - 2, x_max + 4],
        showgrid=False, zeroline=False, showticklabels=False
    )
    fig.update_yaxes(
        range=[y_min - 3, y_max + 3],
        showgrid=False, zeroline=False, showticklabels=False,
        scaleanchor="x", scaleratio=1
    )

    fig.update_layout(
        plot_bgcolor=grass_color,
        paper_bgcolor=grass_color,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(color="#FFFFFF", size=11)
        )
    )

    return fig

def plot_interactive_shotmap(df_shots: pd.DataFrame, title: str = "Mapa Interativo de Finalizações") -> go.Figure:
    fig = create_plotly_pitch_figure(half_pitch=True)
    
    if df_shots.empty:
        fig.update_layout(title=dict(text=f"{title} (Nenhum dado encontrado)", font=dict(color="#FFFFFF")))
        return fig

    # Converter coordenadas para metros na metade atacante
    shots = df_shots.copy()
    shots["pitch_x"] = 105.0 - (shots["x_pct"] * 1.05)
    shots["pitch_y"] = (shots["y_pct"] / 100.0) * 68.0

    # Calcular tamanho da bolha proporcional ao xG (mínimo 6, máximo 28)
    shots["marker_size"] = np.clip(np.sqrt(shots["xg"]) * 35, 6, 28)

    # Agrupar por desfecho para gerar legenda bonita
    for outcome, color in COLOR_OUTCOME_MAP.items():
        subset = shots[shots["outcome"] == outcome]
        if subset.empty:
            continue

        hover_text = []
        for _, row in subset.iterrows():
            xgot_str = f"{row.get('xgot', 0.0):.3f}" if pd.notnull(row.get('xgot')) else "N/A"
            txt = (
                f"<b>{row['player_name']}</b> ({row['shooter_team']})<br>"
                f"Minuto: {row['minute']}' (+{row['added_time']})<br>"
                f"xG: <b>{row['xg']:.3f}</b> | xGOT: {xgot_str}<br>"
                f"Distância: {row['distance_meters']:.1f}m | Ângulo: {row['angle_degrees']:.1f}°<br>"
                f"Situação: {row['situation']} | Parte: {row['body_part']}<br>"
                f"Estado do Jogo: {row['detailed_game_state']} (Placar: {row['score_palmeiras_before']}x{row['score_opponent_before']})<br>"
                f"Adversário: {row['opponent_team']}"
            )
            hover_text.append(txt)

        fig.add_trace(go.Scatter(
            x=subset["pitch_x"],
            y=subset["pitch_y"],
            mode="markers",
            name=outcome,
            marker=dict(
                size=subset["marker_size"],
                color=color,
                opacity=0.85,
                line=dict(color="#FFFFFF", width=1.2 if outcome == "Gol" else 0.5)
            ),
            text=hover_text,
            hoverinfo="text"
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(color="#FFFFFF", size=15), x=0.05, y=0.98)
    )
    return fig
