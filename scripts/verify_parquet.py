import pandas as pd

df_m = pd.read_parquet("data/processed/matches.parquet")
df_s = pd.read_parquet("data/processed/shots.parquet")

print("=== MATCHES SUMMARY ===")
print(f"Total Matches: {len(df_m)}")
print(f"Matches with xG: {(df_m['palmeiras_xg'] > 0).sum()}")
print("Tournaments:", df_m["tournament"].value_counts().to_dict())
print(df_m[["date", "tournament", "home_team", "away_team", "result", "palmeiras_score", "opponent_score", "palmeiras_xg", "opponent_xg"]].head(6))

print("\n=== SHOTS SUMMARY ===")
print(f"Total Shots: {len(df_s)}")
print(f"Palmeiras Shots: {(df_s['is_palmeiras'] == True).sum()}")
print(f"Opponent Shots: {(df_s['is_palmeiras'] == False).sum()}")
print(f"Palmeiras Total xG: {df_s[df_s['is_palmeiras'] == True]['xg'].sum():.2f}")
print(f"Palmeiras Goals: {df_s[df_s['is_palmeiras'] == True]['is_goal'].sum()}")
print("\nSituações:")
print(df_s[df_s["is_palmeiras"] == True]["situation"].value_counts().to_dict())
print("\nGame State ao Chutar:")
print(df_s[df_s["is_palmeiras"] == True]["game_state"].value_counts().to_dict())
print("\nTop 5 Finalizadores (Palmeiras):")
top_shooters = df_s[df_s["is_palmeiras"] == True].groupby("player_name").agg(
    chutes=("shot_id", "count"),
    gols=("is_goal", "sum"),
    xg_total=("xg", "sum")
).sort_values(by="xg_total", ascending=False).head(5)
print(top_shooters)
