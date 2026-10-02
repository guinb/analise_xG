import pandas as pd
import numpy as np

m = pd.read_parquet('data/processed/matches.parquet')
s = pd.read_parquet('data/processed/shots.parquet')
pal_s = s[s['is_palmeiras'] == True]

# Test with 2026 1º Turno vs 2º Turno
bra26 = m[(m['season'] == '2026') & (m['tournament'].str.contains('Brasileir', case=False))]
m_base = bra26[bra26['turno'] == '1º Turno']
m_target = bra26[bra26['turno'] == '2º Turno']

s_base = pal_s[pal_s['match_id'].isin(m_base['match_id'])]
s_target = pal_s[pal_s['match_id'].isin(m_target['match_id'])]

# Causal Metrics
n_mb = len(m_base)
n_mt = len(m_target)

# Team Goals & xG
g_base = m_base['palmeiras_goals'].sum()
gc_base = m_base['opponent_goals'].sum()
xg_pro_base = m_base['palmeiras_xg'].sum()
xg_opp_base = m_base['opponent_xg'].sum()

g_target = m_target['palmeiras_goals'].sum()
gc_target = m_target['opponent_goals'].sum()
xg_pro_target = m_target['palmeiras_xg'].sum()
xg_opp_target = m_target['opponent_xg'].sum()

print("Base:")
print(f"  Jogos: {n_mb} | Gols Pró/j: {g_base/n_mb:.2f} | xG Pró/j: {xg_pro_base/n_mb:.2f}")
print(f"  Gols Contra/j: {gc_base/n_mb:.2f} | xG Contra/j: {xg_opp_base/n_mb:.2f}")
print(f"  Saldo xG/j: {(xg_pro_base - xg_opp_base)/n_mb:+.2f} | Saldo Real/j: {(g_base - gc_base)/n_mb:+.2f}")

print("Target:")
print(f"  Jogos: {n_mt} | Gols Pró/j: {g_target/n_mt:.2f} | xG Pró/j: {xg_pro_target/n_mt:.2f}")
print(f"  Gols Contra/j: {gc_target/n_mt:.2f} | xG Contra/j: {xg_opp_target/n_mt:.2f}")
print(f"  Saldo xG/j: {(xg_pro_target - xg_opp_target)/n_mt:+.2f} | Saldo Real/j: {(g_target - gc_target)/n_mt:+.2f}")

# Player Level
pb = s_base.groupby('player_name').agg(xg_b=('xg','sum'), gols_b=('is_goal','sum'), chutes_b=('shot_id','count')).reset_index()
pt = s_target.groupby('player_name').agg(xg_t=('xg','sum'), gols_t=('is_goal','sum'), chutes_t=('shot_id','count')).reset_index()

pm = pd.merge(pb, pt, on='player_name', how='outer').fillna(0)
pm['delta_xg'] = pm['xg_t'] - pm['xg_b']
pm['delta_gols'] = pm['gols_t'] - pm['gols_b']
pm['diff_eff_b'] = pm['gols_b'] - pm['xg_b']
pm['diff_eff_t'] = pm['gols_t'] - pm['xg_t']
pm['delta_eff'] = pm['diff_eff_t'] - pm['diff_eff_b']

print("\nTop 5 Maior Crescimento xG:")
print(pm.sort_values(by='delta_xg', ascending=False)[['player_name', 'xg_b', 'xg_t', 'delta_xg', 'delta_gols']].head(5))

print("\nTop 5 Maior Queda xG:")
print(pm.sort_values(by='delta_xg', ascending=True)[['player_name', 'xg_b', 'xg_t', 'delta_xg', 'delta_gols']].head(5))

print("\nLogic test completed successfully!")
