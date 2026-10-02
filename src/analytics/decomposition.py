"""
Módulo de Decomposição de Volume x Qualidade de xG:
- xG/90 = (Shots/90) * (xG/shot)
- Cálculo da distribuição de qualidade (chutes de alta chance vs especulativos)
- Decomposição inter-temporal e por competição
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_volume_quality_metrics(df_shots: pd.DataFrame, df_matches: pd.DataFrame, group_by_col: str = "season") -> pd.DataFrame:
    """
    Calcula as métricas decompostas agrupadas por uma dimensão (ex: temporada ou torneio).
    Considera apenas os chutes do Palmeiras (is_palmeiras == True).
    """
    pal_shots = df_shots[df_shots["is_palmeiras"] == True].copy()
    
    # Contagem de partidas por grupo
    matches_per_group = df_matches.groupby(group_by_col)["match_id"].nunique().reset_index()
    matches_per_group.columns = [group_by_col, "total_matches"]

    # Agregações de chutes
    agg = pal_shots.groupby(group_by_col).agg(
        total_shots=("shot_id", "count"),
        total_xg=("xg", "sum"),
        total_goals=("is_goal", "sum"),
        avg_distance=("distance_meters", "mean"),
        avg_angle=("angle_degrees", "mean"),
        high_danger_shots=("xg_danger", lambda s: (s == "Alta (>=0.30)").sum()),
        low_danger_shots=("xg_danger", lambda s: (s == "Especulativa (<0.04)").sum()),
    ).reset_index()

    merged = pd.merge(agg, matches_per_group, on=group_by_col, how="inner")
    
    # Métricas derivadas
    merged["shots_per_90"] = (merged["total_shots"] / merged["total_matches"]).round(2)
    merged["xg_per_shot"] = (merged["total_xg"] / merged["total_shots"]).round(3)
    merged["xg_per_90"] = (merged["total_xg"] / merged["total_matches"]).round(2)
    merged["goals_per_90"] = (merged["total_goals"] / merged["total_matches"]).round(2)
    merged["conversion_rate"] = ((merged["total_goals"] / merged["total_shots"]) * 100).round(1)
    merged["xg_overperformance"] = (merged["total_goals"] - merged["total_xg"]).round(2)
    merged["pct_high_danger"] = ((merged["high_danger_shots"] / merged["total_shots"]) * 100).round(1)
    merged["pct_low_danger"] = ((merged["low_danger_shots"] / merged["total_shots"]) * 100).round(1)
    merged["avg_distance"] = merged["avg_distance"].round(1)
    merged["avg_angle"] = merged["avg_angle"].round(1)

    return merged
