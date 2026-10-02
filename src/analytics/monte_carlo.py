"""
Simulação Binomial Monte Carlo por Partida:
Gera 10.000 iterações simulando a probabilidade de cada chute tomado por Palmeiras
e adversário virar gol, calculando a distribuição real de probabilidade de
Vitória, Empate, Derrota e Pontos Esperados (xPTS).
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

def simulate_match_outcome(palmeiras_xgs: np.ndarray, opponent_xgs: np.ndarray, n_simulations: int = 10000, seed: int = 42) -> Dict[str, Any]:
    """
    Executa simulação Monte Carlo vetorizada de uma partida.
    """
    rng = np.random.default_rng(seed)

    # Simular gols do Palmeiras
    if len(palmeiras_xgs) > 0:
        pal_sims = rng.random((n_simulations, len(palmeiras_xgs))) < palmeiras_xgs
        pal_goals = np.sum(pal_sims, axis=1)
    else:
        pal_goals = np.zeros(n_simulations, dtype=int)

    # Simular gols do adversário
    if len(opponent_xgs) > 0:
        opp_sims = rng.random((n_simulations, len(opponent_xgs))) < opponent_xgs
        opp_goals = np.sum(opp_sims, axis=1)
    else:
        opp_goals = np.zeros(n_simulations, dtype=int)

    # Probabilidades de resultado
    win_count = np.sum(pal_goals > opp_goals)
    draw_count = np.sum(pal_goals == opp_goals)
    loss_count = np.sum(pal_goals < opp_goals)

    prob_win = win_count / n_simulations
    prob_draw = draw_count / n_simulations
    prob_loss = loss_count / n_simulations

    xpts = (prob_win * 3.0) + (prob_draw * 1.0)

    # Distribuição dos placares mais prováveis (top 5)
    scorelines = [f"{p}x{o}" for p, o in zip(pal_goals, opp_goals)]
    score_series = pd.Series(scorelines).value_counts(normalize=True).head(5)
    top_scorelines = [{"score": s, "prob": round(float(p) * 100, 1)} for s, p in score_series.items()]

    return {
        "prob_win": round(prob_win * 100, 1),
        "prob_draw": round(prob_draw * 100, 1),
        "prob_loss": round(prob_loss * 100, 1),
        "xpts": round(xpts, 2),
        "simulated_palmeiras_goals_mean": round(float(np.mean(pal_goals)), 2),
        "simulated_opponent_goals_mean": round(float(np.mean(opp_goals)), 2),
        "top_scorelines": top_scorelines
    }

def simulate_all_matches(df_shots: pd.DataFrame, df_matches: pd.DataFrame, n_simulations: int = 5000) -> pd.DataFrame:
    """
    Roda a simulação para todas as partidas da base e anexa as probabilidades e xPTS ao DataFrame de partidas.
    """
    results = []
    
    for _, match in df_matches.iterrows():
        m_id = match["match_id"]
        m_shots = df_shots[df_shots["match_id"] == m_id]
        
        pal_xgs = m_shots[m_shots["is_palmeiras"] == True]["xg"].values
        opp_xgs = m_shots[m_shots["is_palmeiras"] == False]["xg"].values
        
        sim = simulate_match_outcome(pal_xgs, opp_xgs, n_simulations=n_simulations)
        
        # Pontos reais conquistados
        if match["palmeiras_score"] > match["opponent_score"]:
            real_pts = 3
        elif match["palmeiras_score"] == match["opponent_score"]:
            real_pts = 1
        else:
            real_pts = 0

        results.append({
            "match_id": m_id,
            "prob_win": sim["prob_win"],
            "prob_draw": sim["prob_draw"],
            "prob_loss": sim["prob_loss"],
            "xpts": sim["xpts"],
            "real_pts": real_pts,
            "pts_diff": round(real_pts - sim["xpts"], 2),
            "top_scoreline": sim["top_scorelines"][0]["score"] if sim["top_scorelines"] else ""
        })

    df_sim = pd.DataFrame(results)
    return pd.merge(df_matches, df_sim, on="match_id", how="left")
