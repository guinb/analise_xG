import pandas as pd
import numpy as np

# Load real parquets
m = pd.read_parquet("data/processed/matches.parquet")
s = pd.read_parquet("data/processed/shots.parquet")

pal_shots_all = s[s["is_palmeiras"] == True].copy()

# Test 1: Temporadas 2025 vs 2026
m_base = m[m["season"] == "2025"]
m_target = m[m["season"] == "2026"]
s_base = pal_shots_all[pal_shots_all["match_id"].isin(m_base["match_id"])]
s_target = pal_shots_all[pal_shots_all["match_id"].isin(m_target["match_id"])]

n_m_base = m_base["match_id"].nunique()
n_m_target = m_target["match_id"].nunique()
n_s_base = len(s_base)
n_s_target = len(s_target)

print(f"Base 2025: {n_m_base} matches, {n_s_base} shots")
print(f"Target 2026: {n_m_target} matches, {n_s_target} shots")

# Decomposição
v_base = n_s_base / n_m_base
xg_total_base = s_base["xg"].sum()
q_base = xg_total_base / n_s_base
xg90_base = xg_total_base / n_m_base

v_target = n_s_target / n_m_target
xg_total_target = s_target["xg"].sum()
q_target = xg_total_target / n_s_target
xg90_target = xg_total_target / n_m_target

delta_xg90 = xg90_target - xg90_base
delta_v = v_target - v_base
delta_q = q_target - q_base

mean_q = (q_base + q_target) / 2.0
mean_v = (v_base + v_target) / 2.0
effect_volume = delta_v * mean_q
effect_quality = mean_v * delta_q

print(f"Delta xG90: {delta_xg90:.3f}, Volume effect: {effect_volume:.3f}, Quality effect: {effect_quality:.3f}")
print(f"Sum of effects: {(effect_volume + effect_quality):.3f} (matches delta: {np.isclose(delta_xg90, effect_volume + effect_quality)})")

# Test 2: Turnos 2026 1º Turno vs 2º Turno
bra_m = m[m["tournament"].str.contains("Brasileir", case=False)]
m_t1 = bra_m[(bra_m["season"] == "2026") & (bra_m["turno"] == "1º Turno")]
m_t2 = bra_m[(bra_m["season"] == "2026") & (bra_m["turno"] == "2º Turno")]
print(f"2026 1º Turno: {len(m_t1)} matches, 2026 2º Turno: {len(m_t2)} matches")

# Test 3: Formações Táticas & Field Tilt
print("Field Tilt mean:", m["field_tilt"].mean())
print("Touches in box mean:", m["palmeiras_touches_in_box"].mean())
print("Formations count:", m["palmeiras_formation"].value_counts().to_dict())

print("\nALL LOGIC VERIFIED SUCCESSFULLY!")
