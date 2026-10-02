"""
Módulo para orquestrar a busca de partidas do Palmeiras e seus respectivos
shotmaps e incidentes na API do SofaScore.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.ingestion.sofascore_client import SofaScoreClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PALMEIRAS_ID = 1963

TOURNAMENT_MAP = {
    "Brasileirão Betano": "Brasileirão Série A",
    "Brasileiro Serie A": "Brasileirão Série A",
    "Paulista Série A1": "Campeonato Paulista",
    "Paulista Série A1 - Playoffs": "Campeonato Paulista",
    "CONMEBOL Libertadores, Group F": "Libertadores",
    "CONMEBOL Libertadores, Group G": "Libertadores",
    "CONMEBOL Libertadores, Group C": "Libertadores",
    "CONMEBOL Libertadores, Knockout stage": "Libertadores",
    "Copa Betano do Brasil": "Copa do Brasil",
    "Copa do Brasil": "Copa do Brasil",
    "Supercopa do Brasil": "Supercopa do Brasil",
    "FIFA Club World Cup, Group A": "Mundial de Clubes",
    "FIFA Club World Cup, Knockout stage": "Mundial de Clubes",
}

def normalize_tournament_name(raw_name: str) -> str:
    for key, mapped in TOURNAMENT_MAP.items():
        if key.lower() in raw_name.lower():
            return mapped
    return raw_name

def discover_all_matches(client: SofaScoreClient, max_pages: int = 10) -> List[Dict]:
    """Varre as páginas de eventos recentes do Palmeiras."""
    matches = []
    seen_ids = set()
    
    logger.info(f"Descobrindo partidas do Palmeiras (ID {PALMEIRAS_ID}) em ate {max_pages} paginas...")
    for page in range(max_pages):
        data = client.get_team_events_page(PALMEIRAS_ID, page, force_refresh=(page == 0))
        if not data or "events" not in data or not data["events"]:
            logger.info(f"Fim da paginacao na pagina {page}.")
            break
        
        events = data["events"]
        page_count = 0
        for ev in events:
            ev_id = ev.get("id")
            if ev_id not in seen_ids:
                seen_ids.add(ev_id)
                matches.append(ev)
                page_count += 1
                
        logger.info(f"Pagina {page}: {page_count} novas partidas adicionadas (Total acumulado: {len(matches)})")
        
    return matches

def filter_matches(matches: List[Dict], target_seasons: Optional[List[str]] = None, finished_only: bool = True) -> List[Dict]:
    filtered = []
    for ev in matches:
        # Filtrar status
        status = ev.get("status", {}).get("type")
        if finished_only and status != "finished":
            continue
            
        # Extrair ano da temporada
        season = str(ev.get("season", {}).get("year", "")) or str(ev.get("season", {}).get("name", ""))
        # Se contiver 2024/2025 ou algo assim, extrair os 4 dígitos
        matched_season = None
        for y in ["2023", "2024", "2025", "2026"]:
            if y in season:
                matched_season = y
                break
                
        if not matched_season:
            # Fallback para o startTimestamp se não achou ano no season
            ts = ev.get("startTimestamp")
            if ts:
                import datetime
                year = str(datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).year)
                if year in ["2023", "2024", "2025", "2026"]:
                    matched_season = year
                    
        if not matched_season:
            continue
            
        if target_seasons and matched_season not in target_seasons:
            continue
            
        ev["_computed_season"] = matched_season
        ev["_clean_tournament"] = normalize_tournament_name(ev.get("tournament", {}).get("name", ""))
        filtered.append(ev)
        
    return filtered

def fetch_events_data(client: SofaScoreClient, matches: List[Dict]) -> Dict[str, int]:
    """Baixa shotmap e incidentes para a lista de partidas selecionadas."""
    stats = {
        "total_matches": len(matches),
        "shotmaps_success": 0,
        "shotmaps_missing": 0,
        "with_xg": 0,
        "incidents_success": 0,
    }
    
    for i, ev in enumerate(matches):
        ev_id = ev.get("id")
        season = ev.get("_computed_season", "general")
        home = ev.get("homeTeam", {}).get("name", "")
        away = ev.get("awayTeam", {}).get("name", "")
        tourn = ev.get("_clean_tournament", "")
        
        logger.info(f"[{i+1}/{len(matches)}] Baixando dados para {ev_id}: {home} x {away} ({tourn} {season})...")
        
        # 1. Shotmap
        shotmap_data = client.get_event_shotmap(ev_id, season_year=season)
        if shotmap_data and "shotmap" in shotmap_data and shotmap_data["shotmap"]:
            stats["shotmaps_success"] += 1
            has_xg = any("xg" in s for s in shotmap_data["shotmap"])
            if has_xg:
                stats["with_xg"] += 1
        else:
            stats["shotmaps_missing"] += 1
            
        # 2. Incidentes
        incidents_data = client.get_event_incidents(ev_id, season_year=season)
        if incidents_data and "incidents" in incidents_data:
            stats["incidents_success"] += 1
            
    logger.info(f"Resumo da Ingestao: {stats}")
    return stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestão de dados de partidas e shotmaps do Palmeiras")
    parser.add_argument("--seasons", nargs="+", default=["2024"], help="Temporadas alvo (ex: 2024 ou 2023 2024 2025 2026)")
    parser.add_argument("--pages", type=int, default=8, help="Número de páginas para varredura de eventos")
    args = parser.parse_args()

    client = SofaScoreClient(delay_seconds=0.6)
    all_matches = discover_all_matches(client, max_pages=args.pages)
    target_matches = filter_matches(all_matches, target_seasons=args.seasons)
    logger.info(f"Partidas encontradas para as temporadas {args.seasons}: {len(target_matches)}")
    fetch_events_data(client, target_matches)
