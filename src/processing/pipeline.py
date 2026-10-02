"""
Pipeline principal de processamento:
Consolida os JSONs brutos da pasta data/raw/, aplica o motor de Game State
e a engenharia de features, gerando as tabelas finais em formato Parquet:
- data/processed/matches.parquet
- data/processed/shots.parquet
"""

import datetime
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from src.processing.game_state_engine import (
    parse_match_goals_timeline,
    get_score_before_time,
    classify_game_state,
    calculate_match_minutes_by_state,
)
from src.processing.feature_engineering import (
    calculate_shot_geometry,
    classify_xg_danger,
    normalize_situation,
    normalize_body_part,
    normalize_shot_outcome,
)
from src.processing.advanced_metrics_parser import (
    parse_match_statistics,
    parse_match_lineups,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
PALMEIRAS_ID = 1963

def load_cached_events(raw_dir: Path) -> List[Dict]:
    events = []
    seen = set()
    events_dir = raw_dir / "team_events"
    if not events_dir.exists():
        return events

    for f in sorted(events_dir.glob("events_page_*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                for ev in data.get("events", []):
                    ev_id = ev.get("id")
                    if ev_id and ev_id not in seen:
                        seen.add(ev_id)
                        events.append(ev)
        except Exception as e:
            logger.warning(f"Erro ao ler {f}: {e}")
            
    return events

def run_processing_pipeline(seasons: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    all_events = load_cached_events(RAW_DIR)
    
    matches_rows = []
    shots_rows = []

    logger.info(f"Processando partidas cacheadas ({len(all_events)} encontradas)...")

    for ev in all_events:
        status = ev.get("status", {}).get("type")
        if status != "finished":
            continue

        ev_id = ev.get("id")
        raw_season = str(ev.get("season", {}).get("year", "")) or str(ev.get("season", {}).get("name", ""))
        
        # Identificar ano
        season_year = None
        for y in ["2023", "2024", "2025", "2026"]:
            if y in raw_season:
                season_year = y
                break
        if not season_year and ev.get("startTimestamp"):
            ts = ev.get("startTimestamp")
            dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
            y_str = str(dt.year)
            if y_str in ["2023", "2024", "2025", "2026"]:
                season_year = y_str

        if not season_year:
            continue
        if seasons and season_year not in seasons:
            continue

        # Verificar se os arquivos de shotmap e incidentes existem
        shotmap_file = RAW_DIR / season_year / f"event_{ev_id}_shotmap.json"
        incidents_file = RAW_DIR / season_year / f"event_{ev_id}_incidents.json"

        if not shotmap_file.exists():
            continue

        # Ler JSONs
        try:
            with open(shotmap_file, "r", encoding="utf-8") as f:
                shotmap_json = json.load(f)
        except Exception:
            continue

        incidents_json = {}
        if incidents_file.exists():
            try:
                with open(incidents_file, "r", encoding="utf-8") as f:
                    incidents_json = json.load(f)
            except Exception:
                pass

        # Estatísticas avançadas e escalações
        stats_file = RAW_DIR / season_year / f"event_{ev_id}_statistics.json"
        lineups_file = RAW_DIR / season_year / f"event_{ev_id}_lineups.json"

        stats_json = None
        if stats_file.exists():
            try:
                with open(stats_file, "r", encoding="utf-8") as f:
                    stats_json = json.load(f)
            except Exception:
                pass

        lineups_json = None
        if lineups_file.exists():
            try:
                with open(lineups_file, "r", encoding="utf-8") as f:
                    lineups_json = json.load(f)
            except Exception:
                pass

        # Informações da partida
        home_team = ev.get("homeTeam", {}).get("name", "")
        away_team = ev.get("awayTeam", {}).get("name", "")
        home_id = ev.get("homeTeam", {}).get("id")
        away_id = ev.get("awayTeam", {}).get("id")
        home_score = ev.get("homeScore", {}).get("current", 0) or 0
        away_score = ev.get("awayScore", {}).get("current", 0) or 0
        
        is_palmeiras_home = (home_id == PALMEIRAS_ID)
        palmeiras_score = home_score if is_palmeiras_home else away_score
        opponent_score = away_score if is_palmeiras_home else home_score
        opponent_name = away_team if is_palmeiras_home else home_team

        # Resultado
        if palmeiras_score > opponent_score:
            result = "Vitória"
        elif palmeiras_score == opponent_score:
            result = "Empate"
        else:
            result = "Derrota"

        # Torneio
        t_name = ev.get("tournament", {}).get("name", "")
        from src.ingestion.fetch_data import normalize_tournament_name
        tournament_clean = normalize_tournament_name(t_name)

        # Data
        date_str = ""
        if ev.get("startTimestamp"):
            dt = datetime.datetime.fromtimestamp(ev["startTimestamp"], tz=datetime.timezone.utc)
            date_str = dt.strftime("%Y-%m-%d")

        # Game State
        incidents = incidents_json.get("incidents", [])
        goals_timeline = parse_match_goals_timeline(incidents, is_palmeiras_home)
        minutes_by_state = calculate_match_minutes_by_state(goals_timeline, is_palmeiras_home)

        # Processar chutes
        raw_shots = shotmap_json.get("shotmap", [])
        palmeiras_shots_count = 0
        opponent_shots_count = 0
        palmeiras_xg_sum = 0.0
        opponent_xg_sum = 0.0
        palmeiras_goals_count = 0
        opponent_goals_count = 0

        for s in raw_shots:
            shot_id = s.get("id")
            shot_is_home = s.get("isHome", False)
            is_palmeiras = (shot_is_home == is_palmeiras_home)
            shooter_team = "Palmeiras" if is_palmeiras else opponent_name
            
            outcome_info = normalize_shot_outcome(s.get("shotType", ""))
            is_goal = outcome_info["is_goal"]
            
            xg = float(s.get("xg", 0.0) or 0.0)
            xgot = float(s.get("xgot", 0.0) or 0.0) if s.get("xgot") is not None else None
            
            minute = s.get("time", 0)
            added_time = s.get("addedTime", 0)
            time_seconds = s.get("timeSeconds", minute * 60)

            # Placar antes do chute
            h_before, a_before = get_score_before_time(minute, time_seconds, goals_timeline, is_goal_shot=is_goal)
            pal_before = h_before if is_palmeiras_home else a_before
            opp_before = a_before if is_palmeiras_home else h_before
            diff_before = pal_before - opp_before
            state_info = classify_game_state(diff_before)

            # Coordenadas e Geometria
            coords = s.get("playerCoordinates", {})
            x_pct = coords.get("x", 0.0)
            y_pct = coords.get("y", 50.0)
            geom = calculate_shot_geometry(x_pct, y_pct)

            # Contadores agregados
            if is_palmeiras:
                palmeiras_shots_count += 1
                palmeiras_xg_sum += xg
                if is_goal:
                    palmeiras_goals_count += 1
            else:
                opponent_shots_count += 1
                opponent_xg_sum += xg
                if is_goal:
                    opponent_goals_count += 1

            # Player
            player = s.get("player", {})
            goalkeeper = s.get("goalkeeper", {})

            shots_rows.append({
                "shot_id": shot_id,
                "match_id": ev_id,
                "season": season_year,
                "tournament": tournament_clean,
                "date": date_str,
                "is_palmeiras_home": is_palmeiras_home,
                "is_palmeiras": is_palmeiras,
                "shooter_team": shooter_team,
                "opponent_team": opponent_name,
                "player_id": player.get("id"),
                "player_name": player.get("name", "Desconhecido"),
                "player_position": player.get("position", ""),
                "goalkeeper_id": goalkeeper.get("id"),
                "goalkeeper_name": goalkeeper.get("name", ""),
                "minute": minute,
                "added_time": added_time,
                "time_seconds": time_seconds,
                "period": s.get("reversedPeriodTime", 1),
                "shot_type_raw": s.get("shotType", ""),
                "outcome": outcome_info["outcome"],
                "is_goal": is_goal,
                "situation_raw": s.get("situation", ""),
                "situation": normalize_situation(s.get("situation", "")),
                "body_part_raw": s.get("bodyPart", ""),
                "body_part": normalize_body_part(s.get("bodyPart", "")),
                "xg": round(xg, 4),
                "xgot": round(xgot, 4) if xgot is not None else None,
                "xg_danger": classify_xg_danger(xg),
                "xg_overperformance": round((1.0 - xg) if is_goal else (-xg), 4),
                "x_pct": x_pct,
                "y_pct": y_pct,
                "distance_meters": geom["distance_meters"],
                "angle_degrees": geom["angle_degrees"],
                "shot_corridor": geom["shot_corridor"],
                "shot_zone": geom["shot_zone"],
                "distance_band": geom["distance_band"],
                "score_palmeiras_before": pal_before,
                "score_opponent_before": opp_before,
                "score_diff_before": diff_before,
                "game_state": state_info["macro_state"],
                "detailed_game_state": state_info["detailed_state"]
            })

        # Parsing das estatísticas de jogo e escalações
        adv_stats = parse_match_statistics(stats_json, is_palmeiras_home)
        lineups_parsed = parse_match_lineups(lineups_json, is_palmeiras_home)

        match_record = {
            "match_id": ev_id,
            "season": season_year,
            "tournament": tournament_clean,
            "date": date_str,
            "home_team": home_team,
            "away_team": away_team,
            "is_palmeiras_home": is_palmeiras_home,
            "opponent_name": opponent_name,
            "home_score": home_score,
            "away_score": away_score,
            "palmeiras_score": palmeiras_score,
            "opponent_score": opponent_score,
            "result": result,
            "palmeiras_shots": palmeiras_shots_count,
            "opponent_shots": opponent_shots_count,
            "palmeiras_xg": round(palmeiras_xg_sum, 3),
            "opponent_xg": round(opponent_xg_sum, 3),
            "xg_diff": round(palmeiras_xg_sum - opponent_xg_sum, 3),
            "palmeiras_goals": palmeiras_goals_count,
            "opponent_goals": opponent_goals_count,
            "minutes_winning": minutes_by_state.get("Vencendo", 0.0),
            "minutes_drawing": minutes_by_state.get("Empatando", 0.0),
            "minutes_losing": minutes_by_state.get("Perdendo", 0.0),
            "has_shotmap": len(raw_shots) > 0,
            "has_xg": (palmeiras_xg_sum > 0 or opponent_xg_sum > 0),
            "palmeiras_formation": lineups_parsed["palmeiras_formation"],
            "opponent_formation": lineups_parsed["opponent_formation"],
            "palmeiras_possession": adv_stats["palmeiras_possession"],
            "opponent_possession": adv_stats["opponent_possession"],
            "palmeiras_touches_in_box": adv_stats["palmeiras_touches_in_box"],
            "opponent_touches_in_box": adv_stats["opponent_touches_in_box"],
            "palmeiras_final_third_entries": adv_stats["palmeiras_final_third_entries"],
            "opponent_final_third_entries": adv_stats["opponent_final_third_entries"],
            "field_tilt": adv_stats["field_tilt"],
            "palmeiras_crosses_attempted": adv_stats["palmeiras_crosses_attempted"],
            "palmeiras_crosses_acc_pct": adv_stats["palmeiras_crosses_acc_pct"],
            "opponent_crosses_attempted": adv_stats["opponent_crosses_attempted"],
            "palmeiras_through_balls": adv_stats["palmeiras_through_balls"],
            "opponent_through_balls": adv_stats["opponent_through_balls"],
            "palmeiras_recoveries": adv_stats["palmeiras_recoveries"],
            "opponent_recoveries": adv_stats["opponent_recoveries"],
            "palmeiras_interceptions": adv_stats["palmeiras_interceptions"],
            "opponent_interceptions": adv_stats["opponent_interceptions"],
            "palmeiras_tackles_won_pct": adv_stats["palmeiras_tackles_won_pct"],
            "palmeiras_aerial_won_pct": adv_stats["palmeiras_aerial_won_pct"],
            "opponent_aerial_won_pct": adv_stats["opponent_aerial_won_pct"],
            "palmeiras_ground_won_pct": adv_stats["palmeiras_ground_won_pct"],
            "palmeiras_goals_prevented": adv_stats["palmeiras_goals_prevented"],
            "opponent_goals_prevented": adv_stats["opponent_goals_prevented"],
            "big_chances_palmeiras": adv_stats["big_chances_palmeiras"],
            "big_chances_opponent": adv_stats["big_chances_opponent"],
            "has_advanced_stats": adv_stats["has_advanced_stats"]
        }
        matches_rows.append(match_record)

    df_matches = pd.DataFrame(matches_rows)
    df_shots = pd.DataFrame(shots_rows)

    # Ordenar partidas por data e atribuir round_num e turno
    if not df_matches.empty:
        df_matches = df_matches.sort_values(by=["date", "match_id"]).reset_index(drop=True)
        df_matches["round_num"] = 0
        df_matches["turno"] = "Geral"

        for (s_yr, t_name), grp in df_matches.groupby(["season", "tournament"]):
            idxs = grp.index
            is_bra = "brasileir" in t_name.lower()
            is_pau = "paulista" in t_name.lower()
            is_lib = "libertadores" in t_name.lower()

            for i, idx in enumerate(idxs, start=1):
                df_matches.loc[idx, "round_num"] = i
                if is_bra:
                    df_matches.loc[idx, "turno"] = "1º Turno" if i <= 19 else "2º Turno"
                elif is_pau:
                    df_matches.loc[idx, "turno"] = "Fase de Grupos" if i <= 12 else "Playoffs"
                elif is_lib:
                    df_matches.loc[idx, "turno"] = "Fase de Grupos" if i <= 6 else "Mata-Mata"
                else:
                    df_matches.loc[idx, "turno"] = "Mata-Mata"

        # Propagar round_num e turno para shots
        if not df_shots.empty:
            match_meta = df_matches[["match_id", "round_num", "turno"]]
            df_shots = pd.merge(df_shots, match_meta, on="match_id", how="left")

    # Salvar Parquet
    matches_path = PROCESSED_DIR / "matches.parquet"
    shots_path = PROCESSED_DIR / "shots.parquet"

    df_matches.to_parquet(matches_path, index=False)
    df_shots.to_parquet(shots_path, index=False)

    logger.info(f"Pipeline concluido!")
    logger.info(f" - Matches salvos em {matches_path}: {len(df_matches)} registros")
    logger.info(f" - Shots salvos em {shots_path}: {len(df_shots)} finalizacoes")

    return {"matches": df_matches, "shots": df_shots}

if __name__ == "__main__":
    run_processing_pipeline()
