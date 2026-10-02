import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from src.analytics.decomposition import calculate_volume_quality_metrics
from src.analytics.monte_carlo import simulate_match_outcome, simulate_all_matches
from src.analytics.player_metrics import calculate_player_summary
from src.visualization.pitch_plotly import plot_interactive_shotmap
from src.visualization.pitch_mplsoccer import create_mplsoccer_shotmap

df_m = pd.read_parquet("data/processed/matches.parquet")
df_s = pd.read_parquet("data/processed/shots.parquet")

print("1. Testando Decomposição Volume x Qualidade...")
metrics = calculate_volume_quality_metrics(df_s, df_m, group_by_col="tournament")
print(f" - Decomposição OK: {len(metrics)} torneios processados")

print("2. Testando Métricas de Jogadores...")
players = calculate_player_summary(df_s, min_shots=5)
print(f" - Ranking de Jogadores OK: {len(players)} atletas com >= 5 chutes")

print("3. Testando Simulação Monte Carlo...")
sample_match = df_m[df_m["has_xg"] == True].iloc[0]
m_id = sample_match["match_id"]
m_shots = df_s[df_s["match_id"] == m_id]
pal_xgs = m_shots[m_shots["is_palmeiras"] == True]["xg"].values
opp_xgs = m_shots[m_shots["is_palmeiras"] == False]["xg"].values
sim = simulate_match_outcome(pal_xgs, opp_xgs, n_simulations=1000)
print(f" - Simulação Partida {m_id} ({sample_match['home_team']} x {sample_match['away_team']}): P(V)={sim['prob_win']}%, P(E)={sim['prob_draw']}%, P(D)={sim['prob_loss']}%, xPTS={sim['xpts']}")

print("4. Testando Plotly Pitch...")
fig_plotly = plot_interactive_shotmap(m_shots)
print(f" - Plotly Shotmap OK: {len(fig_plotly.data)} traces criadas")

print("5. Testando Mplsoccer Pitch...")
fig_mpl = create_mplsoccer_shotmap(m_shots[m_shots["is_palmeiras"] == True], title="Teste Mplsoccer")
print(" - Mplsoccer Pitch OK")

print("\nTODOS OS MOTORES ANALÍTICOS E VISUALIZAÇÕES VALIDADOS COM 100% DE SUCESSO!")
