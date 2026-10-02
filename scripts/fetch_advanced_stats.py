"""
Script para baixar de forma incremental e com cache em disco:
1. /event/{id}/statistics (Posse, Toques na área, Entradas no terço final, Cruzamentos, Duelos, Recuperações, Gols evitados)
2. /event/{id}/lineups (Formações táticas, Notas de atletas e escalações)
3. /event/{id}/graph (Attack Momentum / Pressão minuto a minuto)
"""

import sys
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from src.ingestion.sofascore_client import SofaScoreClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def fetch_all_advanced_stats():
    matches_path = ROOT_DIR / "data" / "processed" / "matches.parquet"
    if not matches_path.exists():
        logger.error("matches.parquet não encontrado.")
        return

    df_matches = pd.read_parquet(matches_path)
    total_matches = len(df_matches)
    logger.info(f"Iniciando download de estatísticas avançadas para {total_matches} partidas...")

    client = SofaScoreClient(delay_seconds=0.45)

    stats_ok = 0
    lineups_ok = 0
    graph_ok = 0

    for idx, row in df_matches.iterrows():
        ev_id = int(row["match_id"])
        season = str(row["season"])
        home = row["home_team"]
        away = row["away_team"]

        # 1. Estatísticas
        st_data = client.get_event_statistics(ev_id, season_year=season)
        if st_data and "statistics" in st_data:
            stats_ok += 1

        # 2. Escalações
        ln_data = client.get_event_lineups(ev_id, season_year=season)
        if ln_data and ("home" in ln_data or "away" in ln_data):
            lineups_ok += 1

        # 3. Attack Momentum Graph
        gr_data = client.get_event_graph(ev_id, season_year=season)
        if gr_data and "graphPoints" in gr_data:
            graph_ok += 1

        if (idx + 1) % 25 == 0 or (idx + 1) == total_matches:
            logger.info(f"Progresso: [{idx+1}/{total_matches}] | Stats: {stats_ok} | Lineups: {lineups_ok} | Graphs: {graph_ok}")

    logger.info("Coleta avançada concluída!")
    logger.info(f"Resultados finais: Stats={stats_ok}/{total_matches}, Lineups={lineups_ok}/{total_matches}, Graphs={graph_ok}/{total_matches}")

if __name__ == "__main__":
    fetch_all_advanced_stats()
