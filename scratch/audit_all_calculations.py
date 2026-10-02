import pandas as pd
import numpy as np

df_m = pd.read_parquet("data/processed/matches.parquet")
df_s = pd.read_parquet("data/processed/shots.parquet")

print("="*80)
print("1. AUDITORIA DOS JOGOS DO BRASILEIRÃO 2026")
print("="*80)

bra26 = df_m[(df_m["tournament"].str.contains("Brasileir", case=False, na=False)) & (df_m["season"] == "2026")].sort_values("date")
print(f"Total de jogos Brasileirão 2026: {len(bra26)}")
print("Distribuição por turno:")
print(bra26["turno"].value_counts())

print("\n--- JOGOS DO 2º TURNO 2026 ---")
cols_show = ["date", "opponent_name", "home_team", "away_team", "palmeiras_goals", "opponent_goals", "palmeiras_xg", "opponent_xg", "result", "palmeiras_goals_prevented", "opponent_goals_prevented", "big_chances_palmeiras", "big_chances_opponent"]
t2_m = bra26[bra26["turno"] == "2º Turno"]
print(t2_m[cols_show].to_string())

print("\n--- SOMAS E MÉDIAS DO 2º TURNO 2026 (N = len(t2_m)) ---")
n2 = len(t2_m)
print(f"Número de partidas (n2): {n2}")
print(f"Total Gols Pró: {t2_m['palmeiras_goals'].sum()} | Média: {t2_m['palmeiras_goals'].sum()/n2:.4f} (round 2: {round(t2_m['palmeiras_goals'].sum()/n2, 2)})")
print(f"Total xG Pró (matches): {t2_m['palmeiras_xg'].sum():.4f} | Média: {t2_m['palmeiras_xg'].sum()/n2:.4f} (round 2: {round(t2_m['palmeiras_xg'].sum()/n2, 2)})")
print(f"Total Gols Sofridos: {t2_m['opponent_goals'].sum()} | Média: {t2_m['opponent_goals'].sum()/n2:.4f} (round 2: {round(t2_m['opponent_goals'].sum()/n2, 2)})")
print(f"Total xG Sofrido (matches): {t2_m['opponent_xg'].sum():.4f} | Média: {t2_m['opponent_xg'].sum()/n2:.4f} (round 2: {round(t2_m['opponent_xg'].sum()/n2, 2)})")

print("\n--- CONFERÊNCIA COM TABELA DE CHUTES (SHOTS.PARQUET) ---")
pal_shots = df_s[df_s["is_palmeiras"] == True]
opp_shots = df_s[df_s["is_palmeiras"] == False]

s2_pal = pal_shots[pal_shots["match_id"].isin(t2_m["match_id"])]
s2_opp = opp_shots[opp_shots["match_id"].isin(t2_m["match_id"])]

print(f"Chutes Palmeiras 2ºT: {len(s2_pal)}")
print(f"Soma xG Chutes Palmeiras: {s2_pal['xg'].sum():.4f} | Média/jogo: {s2_pal['xg'].sum()/n2:.4f}")
print(f"Soma Gols Chutes Palmeiras (is_goal): {s2_pal['is_goal'].sum()} | Média/jogo: {s2_pal['is_goal'].sum()/n2:.4f}")

print(f"Chutes Adversários 2ºT: {len(s2_opp)}")
print(f"Soma xG Chutes Adversários: {s2_opp['xg'].sum():.4f} | Média/jogo: {s2_opp['xg'].sum()/n2:.4f}")
print(f"Soma Gols Chutes Adversários (is_goal): {s2_opp['is_goal'].sum()} | Média/jogo: {s2_opp['is_goal'].sum()/n2:.4f}")

print("\n" + "="*80)
print("2. JOGOS DO 1º TURNO 2026")
print("="*80)
t1_m = bra26[bra26["turno"] == "1º Turno"]
n1 = len(t1_m)
print(f"Número de partidas (n1): {n1}")
print(f"Total Gols Pró: {t1_m['palmeiras_goals'].sum()} | Média: {t1_m['palmeiras_goals'].sum()/n1:.4f} (round 2: {round(t1_m['palmeiras_goals'].sum()/n1, 2)})")
print(f"Total xG Pró (matches): {t1_m['palmeiras_xg'].sum():.4f} | Média: {t1_m['palmeiras_xg'].sum()/n1:.4f} (round 2: {round(t1_m['palmeiras_xg'].sum()/n1, 2)})")
print(f"Total Gols Sofridos: {t1_m['opponent_goals'].sum()} | Média: {t1_m['opponent_goals'].sum()/n1:.4f} (round 2: {round(t1_m['opponent_goals'].sum()/n1, 2)})")
print(f"Total xG Sofrido (matches): {t1_m['opponent_xg'].sum():.4f} | Média: {t1_m['opponent_xg'].sum()/n1:.4f} (round 2: {round(t1_m['opponent_xg'].sum()/n1, 2)})")

s1_pal = pal_shots[pal_shots["match_id"].isin(t1_m["match_id"])]
s1_opp = opp_shots[opp_shots["match_id"].isin(t1_m["match_id"])]
print(f"Soma xG Chutes Palmeiras 1ºT: {s1_pal['xg'].sum():.4f} | Média/jogo: {s1_pal['xg'].sum()/n1:.4f}")
print(f"Soma Gols Chutes Palmeiras 1ºT (is_goal): {s1_pal['is_goal'].sum()} | Média/jogo: {s1_pal['is_goal'].sum()/n1:.4f}")
print(f"Soma xG Chutes Adversários 1ºT: {s1_opp['xg'].sum():.4f} | Média/jogo: {s1_opp['xg'].sum()/n1:.4f}")
print(f"Soma Gols Chutes Adversários 1ºT (is_goal): {s1_opp['is_goal'].sum()} | Média/jogo: {s1_opp['is_goal'].sum()/n1:.4f}")
