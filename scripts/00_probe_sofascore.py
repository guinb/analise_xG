"""
Script de sonda para testar a API do SofaScore utilizando curl_cffi:
1. Testa conectividade e impersonation TLS do Chrome.
2. Identifica o ID do Palmeiras e mapeia as competições.
3. Busca partidas recentes do Palmeiras.
4. Testa a disponibilidade e estrutura do shotmap (/event/{id}/shotmap) e dos incidentes (/event/{id}/incidents).
5. Exibe os campos do shotmap: playerCoordinates, xg, situation, shotType, isHome, etc.
"""

import json
import time
from curl_cffi import requests

BASE_URL = "https://api.sofascore.com/api/v1"

def probe():
    session = requests.Session(impersonate="chrome124")
    
    print("[1] Testando informacoes da equipe 'Palmeiras' (ID: 1963)...")
    team_url = f"{BASE_URL}/team/1963"
    resp = session.get(team_url, timeout=15)
    print(f"Status da busca: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Falha na resposta: {resp.text[:300]}")
        return
    
    team_info = resp.json().get("team", {})
    print(f"Equipe: {team_info.get('name')} | Pais: {team_info.get('country', {}).get('name')} | Fundacao: {team_info.get('foundationDateTimestamp')}")
    
    time.sleep(1)
    
    print("\n[2] Testando listagem dos ultimos jogos do Palmeiras (pagina 0)...")
    events_url = f"{BASE_URL}/team/1963/events/last/0"
    resp = session.get(events_url, timeout=15)
    print(f"Status dos eventos: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Erro ao obter eventos: {resp.text[:300]}")
        return
        
    events_data = resp.json()
    events = events_data.get("events", [])
    print(f"Total de partidas retornadas na pagina 0: {len(events)}")
    
    tournaments_found = set()
    sample_match_with_shotmap = None
    
    print("\n[3] Inspecionando torneios e testando /shotmap das partidas...")
    for ev in events[:3]:
        ev_id = ev.get("id")
        t_name = ev.get("tournament", {}).get("name", "Desconhecido")
        season_name = ev.get("season", {}).get("name", "")
        home_team = ev.get("homeTeam", {}).get("name")
        away_team = ev.get("awayTeam", {}).get("name")
        home_score = ev.get("homeScore", {}).get("current")
        away_score = ev.get("awayScore", {}).get("current")
        tournaments_found.add(t_name)
        
        # Testar shotmap
        shotmap_url = f"{BASE_URL}/event/{ev_id}/shotmap"
        time.sleep(0.8)
        sm_resp = session.get(shotmap_url, timeout=15)
        has_shotmap = False
        shot_count = 0
        xg_present = False
        
        if sm_resp.status_code == 200:
            sm_data = sm_resp.json()
            shots = sm_data.get("shotmap", [])
            shot_count = len(shots)
            has_shotmap = shot_count > 0
            if has_shotmap:
                if not sample_match_with_shotmap:
                    sample_match_with_shotmap = (ev, shots)
                xg_present = any("xg" in s for s in shots)
        
        status_symbol = "OK" if has_shotmap else f"STATUS {sm_resp.status_code}"
        print(f"Partida {ev_id}: {home_team} {home_score} x {away_score} {away_team} | {t_name} ({season_name}) -> Shotmap: {status_symbol} ({shot_count} chutes, xG={xg_present})")

    print(f"\nTorneios identificados na amostra recente: {tournaments_found}")
    
    if sample_match_with_shotmap:
        ev, shots = sample_match_with_shotmap
        print(f"\n[4] Detalhe de exemplo de finalização ({ev.get('homeTeam', {}).get('name')} x {ev.get('awayTeam',{}).get('name')}):")
        # Encontrar um chute com xg se possível
        xg_shots = [s for s in shots if "xg" in s]
        sample_shot = xg_shots[0] if xg_shots else shots[0]
        print(json.dumps(sample_shot, indent=2, ensure_ascii=True))
        
        # Testar incidentes
        ev_id = ev.get("id")
        inc_url = f"{BASE_URL}/event/{ev_id}/incidents"
        time.sleep(0.8)
        inc_resp = session.get(inc_url, timeout=15)
        if inc_resp.status_code == 200:
            incidents = inc_resp.json().get("incidents", [])
            print(f"\nTotal de incidentes encontrados na partida {ev_id}: {len(incidents)}")
            goals = [i for i in incidents if i.get("incidentType") == "goal"]
            print(f"Gols registrados nos incidentes: {len(goals)}")
            for g in goals:
                print(f" - Minuto {g.get('time')}: {g.get('player', {}).get('name')} ({g.get('incidentClass')}, novo placar: {g.get('homeScore')}-{g.get('awayScore')})")
        
    print("\nProbe concluido com sucesso!")

if __name__ == "__main__":
    probe()
