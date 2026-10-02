"""
Visualização estática e editorial de campo de futebol e finalizações usando Mplsoccer e Matplotlib.
Ideal para geração de cards de alta fidelidade visual para exportação e postagem em redes/artigos.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from mplsoccer import VerticalPitch

COLOR_OUTCOME_MAP = {
    "Gol": "#00FF87",         # Verde
    "Defesa": "#00BFFF",      # Azul
    "Para Fora": "#FF4B4B",    # Vermelho
    "Bloqueado": "#FFA500",   # Laranja
    "Trave": "#FFD700",       # Dourado
    "Outro": "#A0A0A0"        # Cinza
}

def create_mplsoccer_shotmap(df_shots: pd.DataFrame, title: str = "Mapa de Finalizações - Palmeiras", subtitle: str = "") -> plt.Figure:
    """
    Cria um campo vertical de meio-campo ofensivo com finalizações destacadas.
    """
    pitch = VerticalPitch(
        pitch_type="custom",
        pitch_length=105,
        pitch_width=68,
        half=True,
        pitch_color="#111625",
        line_color="#434f64",
        linewidth=1.8,
        goal_type="box"
    )

    fig, ax = pitch.draw(figsize=(8, 8))
    fig.patch.set_facecolor("#111625")

    if df_shots.empty:
        ax.set_title(f"{title}\n(Sem dados)", color="white", fontsize=14, pad=15)
        return fig

    shots = df_shots.copy()
    # Em VerticalPitch: X vai de 0 a 105 (com gol em 105 no topo), Y vai de 0 a 68 (lateral)
    pitch_x = 105.0 - (shots["x_pct"] * 1.05)
    pitch_y = (shots["y_pct"] / 100.0) * 68.0
    sizes = np.clip(np.sqrt(shots["xg"]) * 650, 40, 600)

    # Plotar desfechos não-gol primeiro
    non_goals = shots[shots["outcome"] != "Gol"]
    for outcome, color in COLOR_OUTCOME_MAP.items():
        if outcome == "Gol":
            continue
        sub = non_goals[non_goals["outcome"] == outcome]
        if sub.empty:
            continue
        sub_x = 105.0 - (sub["x_pct"] * 1.05)
        sub_y = (sub["y_pct"] / 100.0) * 68.0
        sub_sizes = np.clip(np.sqrt(sub["xg"]) * 650, 40, 600)
        
        pitch.scatter(
            sub_x, sub_y,
            s=sub_sizes,
            color=color,
            alpha=0.65,
            edgecolors="#222b3c",
            linewidth=1,
            label=outcome,
            ax=ax
        )

    # Plotar gols por cima com destaque estelar
    goals = shots[shots["outcome"] == "Gol"]
    if not goals.empty:
        g_x = 105.0 - (goals["x_pct"] * 1.05)
        g_y = (goals["y_pct"] / 100.0) * 68.0
        g_sizes = np.clip(np.sqrt(goals["xg"]) * 800, 100, 750)
        
        pitch.scatter(
            g_x, g_y,
            s=g_sizes,
            color=COLOR_OUTCOME_MAP["Gol"],
            alpha=0.95,
            edgecolors="white",
            linewidth=2.0,
            label="Gol",
            ax=ax,
            zorder=5
        )

    # Título e Legenda
    total_shots = len(shots)
    total_xg = shots["xg"].sum()
    total_goals = shots["is_goal"].sum()
    xg_per_shot = (total_xg / total_shots) if total_shots > 0 else 0

    full_title = f"{title}\n"
    stats_sub = f"Chutes: {total_shots} | Gols: {total_goals} | xG Total: {total_xg:.2f} | xG/Chute: {xg_per_shot:.3f}"
    if subtitle:
        stats_sub = f"{subtitle}\n{stats_sub}"

    ax.text(34, 107.5, full_title, color="white", fontsize=15, fontweight="bold", ha="center")
    ax.text(34, 104.5, stats_sub, color="#9bb0cf", fontsize=10, ha="center")

    leg = ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.05),
        ncol=5,
        facecolor="#182032",
        edgecolor="#323f58",
        fontsize=9,
        labelcolor="white"
    )
    plt.tight_layout()
    return fig
