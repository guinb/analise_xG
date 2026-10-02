from curl_cffi import requests
from collections import Counter

session = requests.Session(impersonate="chrome124")

page = 0
all_events = []
seasons_seen = Counter()
tournaments_seen = Counter()

while page < 8:
    url = f"https://api.sofascore.com/api/v1/team/1963/events/last/{page}"
    r = session.get(url, timeout=10)
    if r.status_code != 200:
        print(f"Stop at page {page}, status {r.status_code}")
        break
    data = r.json()
    events = data.get("events", [])
    if not events:
        print(f"No more events at page {page}")
        break
    all_events.extend(events)
    for ev in events:
        s = ev.get("season", {}).get("year") or ev.get("season", {}).get("name")
        t = ev.get("tournament", {}).get("name")
        seasons_seen[s] += 1
        tournaments_seen[t] += 1
    print(f"Page {page}: fetched {len(events)} events (Total: {len(all_events)})")
    page += 1

print("\n--- SEASONS ---")
for s, c in sorted(seasons_seen.items(), key=lambda x: str(x[0])):
    print(f"Season {s}: {c} partidas")

print("\n--- TOURNAMENTS ---")
for t, c in tournaments_seen.most_common():
    print(f"{t}: {c} partidas")
