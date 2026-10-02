"""
Motor de cálculo de Game State (Estado do Placar).
Reconstrói a evolução cronológica do placar a partir dos incidentes da partida,
determina o estado exato antes de cada finalização e computa os minutos totais
que a equipe passou vencendo, empatando ou perdendo.
"""

from typing import Dict, List, Tuple

def parse_match_goals_timeline(incidents: List[Dict], is_palmeiras_home: bool) -> List[Dict]:
    """
    Extrai a sequência cronológica de gols a partir da lista de incidentes.
    Ordena por minuto e tempo adicional.
    """
    goals = []
    if not incidents:
        return goals

    for inc in incidents:
        if inc.get("incidentType") == "goal":
            minute = inc.get("time", 0)
            added_time = inc.get("addedTime", 0)
            # Ordenação temporal em segundos estimados
            sort_key = minute * 60 + added_time
            home_score = inc.get("homeScore")
            away_score = inc.get("awayScore")
            incident_class = inc.get("incidentClass", "regular")
            
            # Se for gol anulado, ignorar (ex: VAR cancel)
            if incident_class == "disallowedGoal":
                continue

            goals.append({
                "time": minute,
                "addedTime": added_time,
                "sort_key": sort_key,
                "homeScore": home_score,
                "awayScore": away_score,
                "isHome": inc.get("isHome", False),
                "player": inc.get("player", {}).get("name", "Desconhecido")
            })

    goals.sort(key=lambda g: g["sort_key"])
    return goals

def get_score_before_time(time_minute: int, time_seconds: int, goals_timeline: List[Dict], is_goal_shot: bool = False) -> Tuple[int, int]:
    """
    Retorna (home_score, away_score) imediatamente antes de um determinado instante.
    """
    curr_home = 0
    curr_away = 0
    
    shot_time_sec = time_seconds if time_seconds > 0 else time_minute * 60

    for g in goals_timeline:
        g_time_sec = g["sort_key"]
        
        # Se este chute for o próprio gol naquele minuto, o placar antes do chute é o placar antes do gol!
        if is_goal_shot:
            if g_time_sec < shot_time_sec:
                if g["homeScore"] is not None and g["awayScore"] is not None:
                    curr_home = g["homeScore"]
                    curr_away = g["awayScore"]
        else:
            if g_time_sec <= shot_time_sec:
                if g["homeScore"] is not None and g["awayScore"] is not None:
                    curr_home = g["homeScore"]
                    curr_away = g["awayScore"]

    return curr_home, curr_away

def classify_game_state(palmeiras_diff: int) -> Dict[str, str]:
    """Classifica a diferença de gols em categorias macro e detalhadas."""
    if palmeiras_diff >= 2:
        detailed = "Vencendo (2+ gols)"
        macro = "Vencendo"
    elif palmeiras_diff == 1:
        detailed = "Vencendo (1 gol)"
        macro = "Vencendo"
    elif palmeiras_diff == 0:
        detailed = "Empatando"
        macro = "Empatando"
    elif palmeiras_diff == -1:
        detailed = "Perdendo (1 gol)"
        macro = "Perdendo"
    else:
        detailed = "Perdendo (2+ gols)"
        macro = "Perdendo"

    return {
        "macro_state": macro,
        "detailed_state": detailed,
        "score_diff": palmeiras_diff
    }

def calculate_match_minutes_by_state(goals_timeline: List[Dict], is_palmeiras_home: bool, total_minutes: int = 95) -> Dict[str, float]:
    """
    Calcula quantos minutos a partida passou em cada estado (Vencendo, Empatando, Perdendo).
    Garante soma exata igual a total_minutes.
    """
    minutes_in_state = {
        "Vencendo": 0.0,
        "Empatando": 0.0,
        "Perdendo": 0.0
    }

    current_home = 0
    current_away = 0
    last_minute = 0

    for g in goals_timeline:
        g_min = min(g["time"], total_minutes)
        duration = max(0, g_min - last_minute)
        
        # Estado atual durante esse intervalo
        pal_diff = (current_home - current_away) if is_palmeiras_home else (current_away - current_home)
        state = classify_game_state(pal_diff)["macro_state"]
        minutes_in_state[state] += duration
        
        # Atualiza placar
        if g["homeScore"] is not None and g["awayScore"] is not None:
            current_home = g["homeScore"]
            current_away = g["awayScore"]
        last_minute = g_min

    # Tempo restante até o fim do jogo
    duration_final = max(0, total_minutes - last_minute)
    pal_diff = (current_home - current_away) if is_palmeiras_home else (current_away - current_home)
    state = classify_game_state(pal_diff)["macro_state"]
    minutes_in_state[state] += duration_final

    return minutes_in_state
