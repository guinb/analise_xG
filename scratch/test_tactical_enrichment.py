import pandas as pd
import numpy as np

m = pd.read_parquet('data/processed/matches.parquet')
s = pd.read_parquet('data/processed/shots.parquet')

# Test columns in matches
cols = ['match_id', 'season', 'tournament', 'turno', 'palmeiras_goals', 'opponent_goals',
        'palmeiras_xg', 'opponent_xg', 'big_chances_palmeiras', 'big_chances_opponent',
        'palmeiras_goals_prevented', 'opponent_goals_prevented', 'palmeiras_formation', 'field_tilt']

for c in cols:
    assert c in m.columns, f"Missing {c}"

print("All columns confirmed present in matches.parquet!")

# Check big chances and goals prevented in 2026 turnos
bra26 = m[(m['season'] == '2026') & (m['tournament'].str.contains('Brasileir', case=False))]
t1 = bra26[bra26['turno'] == '1º Turno']
t2 = bra26[bra26['turno'] == '2º Turno']

print("\n--- 2026 1º Turno (19 jogos) ---")
print(f"Big Chances Pró/j: {t1['big_chances_palmeiras'].mean():.2f} | Sofridas/j: {t1['big_chances_opponent'].mean():.2f}")
print(f"Goals Prevented Weverton/j: {t1['palmeiras_goals_prevented'].mean():.2f} | Goleiros Rivais/j: {t1['opponent_goals_prevented'].mean():.2f}")

print("\n--- 2026 2º Turno (8 jogos) ---")
print(f"Big Chances Pró/j: {t2['big_chances_palmeiras'].mean():.2f} | Sofridas/j: {t2['big_chances_opponent'].mean():.2f}")
print(f"Goals Prevented Weverton/j: {t2['palmeiras_goals_prevented'].mean():.2f} | Goleiros Rivais/j: {t2['opponent_goals_prevented'].mean():.2f}")

# Check formations metrics
f_agg = m[m['palmeiras_formation'].isin(['4-2-3-1', '3-4-2-1', '4-4-2', '3-4-1-2', '4-3-3'])].groupby('palmeiras_formation').agg(
    jogos=('match_id', 'count'),
    xg_pro=('palmeiras_xg', 'mean'),
    xg_contra=('opponent_xg', 'mean'),
    gols_pro=('palmeiras_goals', 'mean'),
    gols_contra=('opponent_goals', 'mean'),
    tilt=('field_tilt', 'mean')
).reset_index()

f_agg['saldo_xg'] = f_agg['xg_pro'] - f_agg['xg_contra']
f_agg['saldo_gols'] = f_agg['gols_pro'] - f_agg['gols_contra']
print("\n--- Formações Agregadas ---")
print(f_agg)
