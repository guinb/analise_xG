"""
Visualização da Curva de Attack Momentum (Pressão de Ataque Minuto a Minuto).
Combina o gráfico de pressão da partida com os eventos de chutes e gols.
"""

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any

def plot_attack_momentum(
    graph_points: List[Dict[str, Any]],
    match_shots: pd.DataFrame,
    is_palmeiras_home: bool,
    palmeiras_name: str = "Palmeiras",
    opponent_name: str = "Adversário",
    title: str = "Attack Momentum (Pressão Ofensiva Minuto a Minuto)"
) -> go.Figure:
    fig = go.Figure()

    if not graph_points:
        fig.update_layout(title=dict(text=f"{title} (Sem dados de momentum)", font=dict(color="white")))
        return fig

    df_points = pd.DataFrame(graph_points)
    if "minute" not in df_points.columns or "value" not in df_points.columns:
        return fig

    # Normalizar para que valores positivos sempre representem a pressão do Palmeiras
    sign = 1 if is_palmeiras_home else -1
    df_points["palmeiras_pressure"] = df_points["value"] * sign

    # Separar em série positiva (Palmeiras) e negativa (Adversário) para coloração de área
    df_points["pal_val"] = df_points["palmeiras_pressure"].apply(lambda v: max(0, v))
    df_points["opp_val"] = df_points["palmeiras_pressure"].apply(lambda v: min(0, v))

    # Área de Pressão do Palmeiras (Verde)
    fig.add_trace(go.Scatter(
        x=df_points["minute"],
        y=df_points["pal_val"],
        mode="lines",
        line=dict(color="#00FF87", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(0, 255, 135, 0.35)",
        name=f"Pressão {palmeiras_name}",
        hoverinfo="skip"
    ))

    # Área de Pressão do Adversário (Vermelho/Laranja)
    fig.add_trace(go.Scatter(
        x=df_points["minute"],
        y=df_points["opp_val"],
        mode="lines",
        line=dict(color="#FF4B4B", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(255, 75, 75, 0.35)",
        name=f"Pressão {opponent_name}",
        hoverinfo="skip"
    ))

    # Linha zero de neutralidade
    fig.add_hline(y=0, line_dash="solid", line_color="rgba(255,255,255,0.3)", line_width=1)

    # Adicionar os Gols como marcadores destacados no momento exato
    goals = match_shots[match_shots["is_goal"] == True]
    if not goals.empty:
        goal_minutes = []
        goal_y = []
        goal_hover = []
        goal_colors = []

        for _, g in goals.iterrows():
            m = g["minute"]
            is_pal = g["is_palmeiras"]
            # Buscar valor de pressão no minuto
            pts = df_points[df_points["minute"] == m]["palmeiras_pressure"].values
            val_at_m = pts[0] if len(pts) > 0 else (15 if is_pal else -15)
            
            goal_minutes.append(m)
            goal_y.append(val_at_m)
            team_label = palmeiras_name if is_pal else opponent_name
            goal_colors.append("#00FF87" if is_pal else "#FFD700")
            
            goal_hover.append(
                f"⚽ <b>GOL! {g['player_name']} ({team_label})</b><br>"
                f"Minuto: {m}'<br>"
                f"xG: {g['xg']:.3f} | Dist: {g['distance_meters']:.1f}m<br>"
                f"Momentum de Pressão: {val_at_m:+.0f}"
            )

        fig.add_trace(go.Scatter(
            x=goal_minutes,
            y=goal_y,
            mode="markers",
            name="⚽ Gols Marcados",
            marker=dict(
                size=14,
                color=goal_colors,
                symbol="star",
                line=dict(color="white", width=2)
            ),
            text=goal_hover,
            hoverinfo="text"
        ))

    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(color="white", size=15),
            x=0.05, y=0.96
        ),
        xaxis=dict(title="Minuto da Partida", range=[0, 95], showgrid=False),
        yaxis=dict(
            title=f"⬅️ Pressão {opponent_name} | Pressão {palmeiras_name} ➡️",
            range=[-100, 100],
            showgrid=True,
            gridcolor="rgba(255,255,255,0.1)"
        ),
        template="plotly_dark",
        height=320,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )

    return fig
