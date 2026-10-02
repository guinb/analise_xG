"""
Módulo de Métricas e Raio-X por Jogador:
- Volume de finalizações, Gols reais vs xG acumulado
- Diferencial de Conversão (G - xG)
- Qualidade média por finalização (xG/shot)
- Distância média e preferência por parte do corpo
"""

import pandas as pd

def calculate_player_summary(df_shots: pd.DataFrame, min_shots: int = 5) -> pd.DataFrame:
    pal_shots = df_shots[df_shots["is_palmeiras"] == True].copy()
    
    grouped = pal_shots.groupby(["player_id", "player_name", "player_position"]).agg(
        matches_with_shot=("match_id", "nunique"),
        total_shots=("shot_id", "count"),
        total_goals=("is_goal", "sum"),
        total_xg=("xg", "sum"),
        avg_distance=("distance_meters", "mean"),
        avg_angle=("angle_degrees", "mean"),
        shots_right_foot=("body_part", lambda s: (s == "Pé Direito").sum()),
        shots_left_foot=("body_part", lambda s: (s == "Pé Esquerdo").sum()),
        shots_head=("body_part", lambda s: (s == "Cabeça").sum()),
        high_danger_shots=("xg_danger", lambda s: (s == "Alta (>=0.30)").sum()),
        low_danger_shots=("xg_danger", lambda s: (s == "Especulativa (<0.04)").sum()),
    ).reset_index()

    # Filtrar por corte mínimo de chutes
    filtered = grouped[grouped["total_shots"] >= min_shots].copy()

    # Métricas derivadas
    filtered["xg_per_shot"] = (filtered["total_xg"] / filtered["total_shots"]).round(3)
    filtered["conversion_pct"] = ((filtered["total_goals"] / filtered["total_shots"]) * 100).round(1)
    filtered["xg_overperformance"] = (filtered["total_goals"] - filtered["total_xg"]).round(2)
    filtered["pct_high_danger"] = ((filtered["high_danger_shots"] / filtered["total_shots"]) * 100).round(1)
    filtered["pct_low_danger"] = ((filtered["low_danger_shots"] / filtered["total_shots"]) * 100).round(1)
    filtered["avg_distance"] = filtered["avg_distance"].round(1)
    filtered["avg_angle"] = filtered["avg_angle"].round(1)
    filtered["total_xg"] = filtered["total_xg"].round(2)

    return filtered.sort_values(by="total_xg", ascending=False)
