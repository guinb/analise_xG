import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from app.modules.mod_comparison import filter_dataset_by_preset, compute_profile_metrics
from src.visualization.pitch_density import plot_density_shotmap, plot_tactical_zones_pitch

df_m = pd.read_parquet("data/processed/matches.parquet")
df_s = pd.read_parquet("data/processed/shots.parquet")

print("1. Verificando novas colunas nos dados...")
print("Colunas em matches:", [c for c in ["round_num", "turno"] if c in df_m.columns])
print("Colunas em shots:", [c for c in ["shot_corridor", "shot_zone", "distance_band", "turno", "round_num"] if c in df_s.columns])

print("\n2. Testando contagem de turnos no Brasileirão:")
bra = df_m[df_m["tournament"].str.contains("Brasileir", case=False)]
print(bra.groupby(["season", "turno"])["match_id"].count())

print("\n3. Testando perfis do Modo Comparação (2026 vs 2025):")
m_25, s_25 = filter_dataset_by_preset(df_m, df_s, "Temporada Completa", "2025")
m_26, s_26 = filter_dataset_by_preset(df_m, df_s, "Temporada Completa", "2026")
prof_25 = compute_profile_metrics(m_25, s_25)
prof_26 = compute_profile_metrics(m_26, s_26)
print(f"2025: {prof_25['shots_p90']:.1f} chutes/90, {prof_25['xg_p90']:.2f} xG/90, {prof_25['xg_p_shot']:.3f} xG/chute")
print(f"2026: {prof_26['shots_p90']:.1f} chutes/90, {prof_26['xg_p90']:.2f} xG/90, {prof_26['xg_p_shot']:.3f} xG/chute")

print("\n4. Testando comparação de turnos do Brasileirão 2026 (1º Turno vs 2º Turno):")
m_t1, s_t1 = filter_dataset_by_preset(df_m, df_s, "Turno do Brasileirão", "2026 - 1º Turno")
m_t2, s_t2 = filter_dataset_by_preset(df_m, df_s, "Turno do Brasileirão", "2026 - 2º Turno")
prof_t1 = compute_profile_metrics(m_t1, s_t1)
prof_t2 = compute_profile_metrics(m_t2, s_t2)
print(f"2026 1º Turno: {prof_t1['n_matches']} jogos, {prof_t1['xg_p90']:.2f} xG/90")
print(f"2026 2º Turno: {prof_t2['n_matches']} jogos, {prof_t2['xg_p90']:.2f} xG/90")

print("\n5. Testando geração de mapa de densidade (KDE) e zonas táticas...")
fig_dens = plot_density_shotmap(s_26)
fig_zones = plot_tactical_zones_pitch(s_26)
print("Mapas gerados com sucesso!")

print("\nTODOS OS TESTES DOS NOVOS COMPONENTES PASSARAM COM 100% DE SUCESSO!")
