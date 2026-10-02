from curl_cffi import requests
import json

session = requests.Session(impersonate="chrome124")

event_id = 15235550  # Palmeiras 1 x 0 Athletico (Brasileirao 2026)

print("--- 1. TESTANDO /event/{id}/statistics ---")
r_stats = session.get(f"https://api.sofascore.com/api/v1/event/{event_id}/statistics", timeout=10)
print(f"Stats status: {r_stats.status_code}")
if r_stats.status_code == 200:
    data = r_stats.json().get("statistics", [])
    if data:
        all_period = data[0]
        groups = all_period.get("groups", [])
        print(f"Grupos de estatisticas disponíveis: {[g.get('groupName') for g in groups]}")
        for g in groups:
            print(f"\nGrupo: {g.get('groupName')}")
            for item in g.get("statisticsItems", [])[:4]:
                print(f"  - {item.get('name')}: Home {item.get('home')} vs Away {item.get('away')}")

print("\n--- 2. TESTANDO /event/{id}/lineups ---")
r_lineups = session.get(f"https://api.sofascore.com/api/v1/event/{event_id}/lineups", timeout=10)
print(f"Lineups status: {r_lineups.status_code}")
if r_lineups.status_code == 200:
    data_l = r_lineups.json()
    print(f"Formação Home: {data_l.get('home', {}).get('formation')} | Formação Away: {data_l.get('away', {}).get('formation')}")
    players = data_l.get("home", {}).get("players", [])
    if players:
        p0 = players[0]
        p_name = p0.get("player", {}).get("name")
        p_id = p0.get("player", {}).get("id")
        p_rating = p0.get("statistics", {}).get("rating")
        avg_pos = p0.get("averagePositions", [])
        print(f"Exemplo jogador: {p_name} (ID {p_id}), Rating: {p_rating}, Avg Pos: {avg_pos}")

print("\n--- 3. TESTANDO /event/{id}/player/{player_id}/heatmap ---")
# pegar id de jogador de linha
if r_lineups.status_code == 200 and len(players) > 1:
    field_player = players[1]
    fp_id = field_player.get("player", {}).get("id")
    fp_name = field_player.get("player", {}).get("name")
    r_hm = session.get(f"https://api.sofascore.com/api/v1/event/{event_id}/player/{fp_id}/heatmap", timeout=10)
    print(f"Heatmap status para {fp_name} (ID {fp_id}): {r_hm.status_code}")
    if r_hm.status_code == 200:
        hm_points = r_hm.json().get("heatmap", [])
        print(f"Pontos de calor (touches/positions): {len(hm_points)} pontos")
        if hm_points:
            print(f"Amostra ponto: {hm_points[0]}")

print("\n--- 4. TESTANDO /event/{id}/graph (MOMENTUM DE PRESSÃO) ---")
r_graph = session.get(f"https://api.sofascore.com/api/v1/event/{event_id}/graph", timeout=10)
print(f"Graph status: {r_graph.status_code}")
if r_graph.status_code == 200:
    graph_pts = r_graph.json().get("graphPoints", [])
    print(f"Pontos de pressão minuto a minuto: {len(graph_pts)} minutos registrados")
    if graph_pts:
        print(f"Amostra ponto (min {graph_pts[0].get('minute')}): valor {graph_pts[0].get('value')}")
