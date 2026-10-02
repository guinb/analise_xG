import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from app.modules.mod1_decomposition import render_decomposition_tab
from app.modules.mod2_game_state import render_game_state_tab
from app.modules.mod3_creation_phase import render_creation_phase_tab
from app.modules.mod4_simulation import render_simulation_tab
from app.modules.mod5_players import render_players_tab

df_m = pd.read_parquet("data/processed/matches.parquet")
df_s = pd.read_parquet("data/processed/shots.parquet")

print("Validando imports e estrutura de dados...")
print(f"Matches: {len(df_m)}, Shots: {len(df_s)}")
print("Tudo importado com sucesso!")
