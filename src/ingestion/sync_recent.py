"""
Módulo para sincronização automática de novos jogos do Palmeiras a partir da API do SofaScore.
Detecta novos jogos finalizados que ainda não estão no matches.parquet,
baixa todos os dados necessários e roda o pipeline de atualização incremental.
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

from src.ingestion.sofascore_client import SofaScoreClient
from src.processing.pipeline import run_processing_pipeline

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
PALMEIRAS_ID = 1963

def sync_new_matches() -> Tuple[int, List[str]]:
    """
    Verifica se há novos jogos finalizados no SofaScore.
    Retorna (quantidade_novos_jogos, lista_de_mensagens_dos_jogos).
    """
    matches_file = PROCESSED_DIR / "matches.parquet"
    known_ids = set()
    if matches_file.exists():
        df_existing = pd.read_parquet(matches_file)
        known_ids = set(df_existing["match_id"].dropna().unique())

    client = SofaScoreClient(delay_seconds=0.5)

    # 1. Buscar página 0 forçando refresh
    data = client.get_team_events_page(PALMEIRAS_ID, 0, force_refresh=True)
    if not data or "events" not in data:
        return 0, ["Não foi possível contactar a API do SofaScore."]

    new_events = []
    for ev in data.get("events", []):
        status = ev.get("status", {}).get("type")
        ev_id = ev.get("id")
        if status == "finished" and ev_id not in known_ids:
            new_events.append(ev)

    if not new_events:
        return 0, []

    # 2. Baixar dados brutos dos novos jogos
    added_descriptions = []
    for ev in new_events:
        ev_id = ev.get("id")
        ts = ev.get("startTimestamp")
        import datetime
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        season = str(dt.year)

        home = ev.get("homeTeam", {}).get("name", "Mandante")
        away = ev.get("awayTeam", {}).get("name", "Visitante")
        h_score = ev.get("homeScore", {}).get("current", 0)
        a_score = ev.get("awayScore", {}).get("current", 0)
        desc = f"{dt.strftime('%d/%m/%Y')} - {home} {h_score}x{a_score} {away}"
        added_descriptions.append(desc)

        logger.info(f"Baixando dados para novo jogo: {desc} (ID: {ev_id})...")

        # Shotmap
        client.get_event_shotmap(ev_id, season_year=season)
        # Incidentes
        client.get_event_incidents(ev_id, season_year=season)
        # Estatísticas
        client.get_event_statistics(ev_id, season_year=season)
        # Escalações
        client.get_event_lineups(ev_id, season_year=season)
        # Graph
        client.get_event_graph(ev_id, season_year=season)
        # Details
        client.get_event_details(ev_id, season_year=season)

    # 3. Rodar pipeline de dados
    logger.info("Processando novos jogos no pipeline Parquet...")
    run_processing_pipeline(seasons=["2023", "2024", "2025", "2026"])

    return len(new_events), added_descriptions
