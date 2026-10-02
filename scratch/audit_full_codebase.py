import pandas as pd
import numpy as np

df_m = pd.read_parquet("data/processed/matches.parquet")
df_s = pd.read_parquet("data/processed/shots.parquet")

print("="*80)
print("AUDITORIA COMPLETA DE DADOS E CÁLCULOS DO DASHBOARD")
print("="*80)

# 1. Checagem de consistência jogo a jogo entre matches.parquet e shots.parquet
print("\n--- 1. CONSISTÊNCIA ENTRE MATCHES E SHOTS ---")
shot_agg = df_s.groupby(["match_id", "is_palmeiras"]).agg(
    shot_xg=("xg", "sum"),
    shot_goals=("is_goal", "sum"),
    shot_count=("shot_id", "count")
).unstack(fill_value=0)

shot_agg.columns = [f"{col[0]}_{'pal' if col[1] else 'opp'}" for col in shot_agg.columns]
shot_agg = shot_agg.reset_index()

merged = pd.merge(df_m, shot_agg, on="match_id", how="left")

# Comparar xG Palmeiras
diff_pal_xg = (merged["palmeiras_xg"] - merged["shot_xg_pal"]).dropna()
print(f"Diferença máxima de xG Palmeiras entre matches e shots: {diff_pal_xg.abs().max():.6f}")

# Comparar Gols Palmeiras
diff_pal_goals = (merged["palmeiras_goals"] - merged["shot_goals_pal"]).dropna()
goals_mismatches = merged[merged["palmeiras_goals"] != merged["shot_goals_pal"]]
print(f"Jogos com divergência de gols pró entre matches e shots: {len(goals_mismatches)}")
if len(goals_mismatches) > 0:
    print(goals_mismatches[["match_id", "date", "opponent_name", "palmeiras_goals", "shot_goals_pal"]])

# Comparar xG Adversário
diff_opp_xg = (merged["opponent_xg"] - merged["shot_xg_opp"]).dropna()
print(f"Diferença máxima de xG Adversário entre matches e shots: {diff_opp_xg.abs().max():.6f}")

# Comparar Gols Adversário
diff_opp_goals = (merged["opponent_goals"] - merged["shot_goals_opp"]).dropna()
opp_goals_mismatches = merged[merged["opponent_goals"] != merged["shot_goals_opp"]]
print(f"Jogos com divergência de gols contra entre matches e shots: {len(opp_goals_mismatches)}")
if len(opp_goals_mismatches) > 0:
    print(opp_goals_mismatches[["match_id", "date", "opponent_name", "opponent_goals", "shot_goals_opp"]])

# 2. Análise Específica do 1º Turno e 2º Turno 2026
print("\n" + "="*80)
print("2. ANÁLISE DETALHADA: BRASILEIRÃO 2026 (1º TURNO VS 2º TURNO)")
print("="*80)
b26 = df_m[(df_m["tournament"].str.contains("Brasileir", case=False, na=False)) & (df_m["season"] == "2026")]
m1 = b26[b26["turno"] == "1º Turno"]
m2 = b26[b26["turno"] == "2º Turno"]

s_pal = df_s[df_s["is_palmeiras"] == True]
s1 = s_pal[s_pal["match_id"].isin(m1["match_id"])]
s2 = s_pal[s_pal["match_id"].isin(m2["match_id"])]

print(f"\n[1º TURNO 2026 - {len(m1)} jogos]")
print(f"Gols Pró: {m1['palmeiras_goals'].sum()} total -> {m1['palmeiras_goals'].sum()/len(m1):.4f}/j (exibido: {m1['palmeiras_goals'].sum()/len(m1):.2f})")
print(f"xG Pró (shots): {s1['xg'].sum():.4f} total -> {s1['xg'].sum()/len(m1):.4f}/j (exibido: {s1['xg'].sum()/len(m1):.2f})")
print(f"Gols Sofridos: {m1['opponent_goals'].sum()} total -> {m1['opponent_goals'].sum()/len(m1):.4f}/j (exibido: {m1['opponent_goals'].sum()/len(m1):.2f})")
print(f"xG Sofrido (matches): {m1['opponent_xg'].sum():.4f} total -> {m1['opponent_xg'].sum()/len(m1):.4f}/j (exibido: {m1['opponent_xg'].sum()/len(m1):.2f})")

print(f"\n[2º TURNO 2026 - {len(m2)} jogos]")
print(f"Gols Pró: {m2['palmeiras_goals'].sum()} total -> {m2['palmeiras_goals'].sum()/len(m2):.4f}/j (exibido: {m2['palmeiras_goals'].sum()/len(m2):.2f})")
print(f"xG Pró (shots): {s2['xg'].sum():.4f} total -> {s2['xg'].sum()/len(m2):.4f}/j (exibido: {s2['xg'].sum()/len(m2):.2f})")
print(f"Gols Sofridos: {m2['opponent_goals'].sum()} total -> {m2['opponent_goals'].sum()/len(m2):.4f}/j (exibido: {m2['opponent_goals'].sum()/len(m2):.2f})")
print(f"xG Sofrido (matches): {m2['opponent_xg'].sum():.4f} total -> {m2['opponent_xg'].sum()/len(m2):.4f}/j (exibido: {m2['opponent_xg'].sum()/len(m2):.2f})")

print("\n--- POR QUE xG E GOLS DERAM 1.62 NO 2º TURNO? ---")
print(f"Total Gols 2º Turno: {m2['palmeiras_goals'].sum()} em {len(m2)} partidas = {m2['palmeiras_goals'].sum()/len(m2):.6f}")
print(f"Total xG 2º Turno: {s2['xg'].sum():.6f} em {len(m2)} partidas = {s2['xg'].sum()/len(m2):.6f}")
print(f"Diferença exata entre Gols/j e xG/j no 2º Turno: {(m2['palmeiras_goals'].sum()/len(m2)) - (s2['xg'].sum()/len(m2)):+.6f}")
print(f"Ambos arredondados para 2 casas decimais: Gols={m2['palmeiras_goals'].sum()/len(m2):.2f}, xG={s2['xg'].sum()/len(m2):.2f}")

# 3. Conferência de todas as outras métricas da View 2
print("\n--- CONFERÊNCIA DAS OUTRAS MÉTRICAS NA VIEW 2 ---")
# Big Chances
print("Big Chances Palmeiras:")
print(f"1º Turno média: {m1['big_chances_palmeiras'].mean():.4f} (round: {m1['big_chances_palmeiras'].mean():.2f})")
print(f"2º Turno média: {m2['big_chances_palmeiras'].mean():.4f} (round: {m2['big_chances_palmeiras'].mean():.2f})")
print("Big Chances Oponente:")
print(f"1º Turno média: {m1['big_chances_opponent'].mean():.4f} (round: {m1['big_chances_opponent'].mean():.2f})")
print(f"2º Turno média: {m2['big_chances_opponent'].mean():.4f} (round: {m2['big_chances_opponent'].mean():.2f})")

# Goals Prevented
print("Goals Prevented Palmeiras:")
print(f"1º Turno média: {m1['palmeiras_goals_prevented'].mean():.4f} (round: {m1['palmeiras_goals_prevented'].mean():.2f})")
print(f"2º Turno média: {m2['palmeiras_goals_prevented'].mean():.4f} (round: {m2['palmeiras_goals_prevented'].mean():.2f})")
print("Goals Prevented Oponente:")
print(f"1º Turno média: {m1['opponent_goals_prevented'].mean():.4f} (round: {m1['opponent_goals_prevented'].mean():.2f})")
print(f"2º Turno média: {m2['opponent_goals_prevented'].mean():.4f} (round: {m2['opponent_goals_prevented'].mean():.2f})")

# Saldo Real e Esperado
sr1 = (m1['palmeiras_goals'].sum() - m1['opponent_goals'].sum()) / len(m1)
se1 = (s1['xg'].sum() - m1['opponent_xg'].sum()) / len(m1)
sr2 = (m2['palmeiras_goals'].sum() - m2['opponent_goals'].sum()) / len(m2)
se2 = (s2['xg'].sum() - m2['opponent_xg'].sum()) / len(m2)
print("Saldo Real vs Esperado:")
print(f"1º Turno: Saldo Real={sr1:+.4f} (round: {sr1:+.2f}), Saldo xG={se1:+.4f} (round: {se1:+.2f})")
print(f"2º Turno: Saldo Real={sr2:+.4f} (round: {sr2:+.2f}), Saldo xG={se2:+.4f} (round: {se2:+.2f})")

# Letalidade individual
pb = s1.groupby("player_name").agg(xg_b=("xg", "sum"), gols_b=("is_goal", "sum")).reset_index()
pt = s2.groupby("player_name").agg(xg_t=("xg", "sum"), gols_t=("is_goal", "sum")).reset_index()
pm = pd.merge(pb, pt, on="player_name", how="outer").fillna(0)
pm["diff_b"] = pm["gols_b"] - pm["xg_b"]
pm["diff_t"] = pm["gols_t"] - pm["xg_t"]
pm["delta_eff"] = pm["diff_t"] - pm["diff_b"]
print("\nTop 5 Queda de Conversão:")
print(pm.sort_values("delta_eff", ascending=True).head(5)[["player_name", "xg_b", "gols_b", "diff_b", "xg_t", "gols_t", "diff_t", "delta_eff"]].to_string())
