import pandas as pd
import json
import os

m = pd.read_parquet('data/processed/matches.parquet')
print('Matches count:', len(m))

success = 0
for idx, row in m.iterrows():
    p = f"data/raw/{row['season']}/event_{row['match_id']}_lineups.json"
    if not os.path.exists(p):
        continue
    with open(p, encoding='utf-8') as f:
        d = json.load(f)
    side = 'home' if row['is_palmeiras_home'] else 'away'
    if side not in d or 'players' not in d[side]:
        continue
    starters = [x for x in d[side]['players'] if not x.get('substitute')]
    if len(starters) == 11:
        success += 1

print(f"Total matches with exactly 11 starters: {success} / {len(m)}")
