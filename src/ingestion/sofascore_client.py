"""
Cliente para a API do SofaScore utilizando curl_cffi com impersonation do Chrome,
gerenciamento de taxa de requisições e persistência de cache local (JSON bruto).
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
from curl_cffi import requests

logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"

class SofaScoreClient:
    BASE_URL = "https://api.sofascore.com/api/v1"

    def __init__(self, delay_seconds: float = 0.6, cache_dir: Optional[Path] = None):
        self.delay_seconds = delay_seconds
        self.cache_dir = cache_dir or RAW_DATA_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session(impersonate="chrome124")
        self.last_request_time = 0.0

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        self.last_request_time = time.time()

    def get_json(self, endpoint: str, cache_path: Optional[Path] = None, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        # Verificar cache local primeiro
        if cache_path and cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao ler cache {cache_path}: {e}")

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if cache_path:
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(cache_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False)
                    return data
                elif response.status_code == 404:
                    # Endpoint ou recurso inexistente (ex: partida sem shotmap)
                    return None
                elif response.status_code in (403, 429):
                    wait_time = (attempt + 1) * 3
                    logger.warning(f"HTTP {response.status_code} em {url}. Aguardando {wait_time}s antes da tentativa {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"HTTP {response.status_code} ao buscar {url}")
            except Exception as e:
                logger.warning(f"Exceção ao requisitar {url} (tentativa {attempt + 1}): {e}")
                time.sleep((attempt + 1) * 2)

        return None

    def get_team_events_page(self, team_id: int, page: int, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / "team_events" / f"events_page_{page}.json"
        if force_refresh and cache_file.exists():
            try:
                cache_file.unlink()
            except Exception:
                pass
        return self.get_json(f"team/{team_id}/events/last/{page}", cache_path=cache_file)

    def get_event_shotmap(self, event_id: int, season_year: str = "general") -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / str(season_year) / f"event_{event_id}_shotmap.json"
        return self.get_json(f"event/{event_id}/shotmap", cache_path=cache_file)

    def get_event_incidents(self, event_id: int, season_year: str = "general") -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / str(season_year) / f"event_{event_id}_incidents.json"
        return self.get_json(f"event/{event_id}/incidents", cache_path=cache_file)

    def get_event_details(self, event_id: int, season_year: str = "general") -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / str(season_year) / f"event_{event_id}_details.json"
        return self.get_json(f"event/{event_id}", cache_path=cache_file)

    def get_event_statistics(self, event_id: int, season_year: str = "general") -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / str(season_year) / f"event_{event_id}_statistics.json"
        return self.get_json(f"event/{event_id}/statistics", cache_path=cache_file)

    def get_event_lineups(self, event_id: int, season_year: str = "general") -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / str(season_year) / f"event_{event_id}_lineups.json"
        return self.get_json(f"event/{event_id}/lineups", cache_path=cache_file)

    def get_event_graph(self, event_id: int, season_year: str = "general") -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / str(season_year) / f"event_{event_id}_graph.json"
        return self.get_json(f"event/{event_id}/graph", cache_path=cache_file)

    def get_player_heatmap(self, event_id: int, player_id: int, season_year: str = "general") -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / str(season_year) / f"event_{event_id}_player_{player_id}_heatmap.json"
        return self.get_json(f"event/{event_id}/player/{player_id}/heatmap", cache_path=cache_file)
