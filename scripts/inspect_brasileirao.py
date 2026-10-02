import pandas as pd

df_m = pd.read_parquet("data/processed/matches.parquet")
print("Colunas:", df_m.columns.tolist())
bra = df_m[df_m["tournament"].str.contains("Brasileir", case=False, na=False)].sort_values("date")
print(f"Total Brasileirao: {len(bra)}")
print("Por temporada:")
print(bra["season"].value_counts())

for season, grp in bra.groupby("season"):
    print(f"\nTemporada {season}: {len(grp)} jogos de {grp['date'].min()} a {grp['date'].max()}")
    print(grp[["date", "home_team", "away_team", "palmeiras_score", "opponent_score"]].head(2))
