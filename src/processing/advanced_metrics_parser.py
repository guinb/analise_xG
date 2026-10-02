"""
Parser de estatísticas avançadas e escalações da partida:
Extrai posse de bola, toques na área, entradas no terço final, field tilt,
cruzamentos, duelos aéreos, recuperações, formações táticas e gols evitados.
"""

from typing import Dict, Any, Optional

def _parse_val(val_raw: Any) -> float:
    """Extrai valor numérico de strings como '50%', '334 (82%)', '4/15 (27%)', '0.49' ou 18."""
    if val_raw is None:
        return 0.0
    if isinstance(val_raw, (int, float)):
        return float(val_raw)
    s = str(val_raw).strip()
    if "%" in s:
        # Se for "50%", pega 50.0
        # Se for "4/15 (27%)", pega 27.0 ou o primeiro número
        try:
            inside = s.split("(")[-1].replace(")", "").replace("%", "").strip()
            return float(inside)
        except Exception:
            pass
    if "/" in s:
        try:
            return float(s.split("/")[0].strip())
        except Exception:
            pass
    try:
        # Pega a primeira palavra numérica
        first = s.split()[0].replace("%", "").strip()
        return float(first)
    except Exception:
        return 0.0

def parse_match_statistics(stats_json: Optional[Dict[str, Any]], is_palmeiras_home: bool) -> Dict[str, float]:
    """
    Normaliza todas as estatísticas para que métricas 'palmeiras_*' correspondam
    ao time do Palmeiras e 'opponent_*' ao time adversário.
    """
    res = {
        "palmeiras_possession": 50.0,
        "opponent_possession": 50.0,
        "palmeiras_touches_in_box": 0.0,
        "opponent_touches_in_box": 0.0,
        "palmeiras_final_third_entries": 0.0,
        "opponent_final_third_entries": 0.0,
        "field_tilt": 50.0,
        "palmeiras_crosses_attempted": 0.0,
        "palmeiras_crosses_acc_pct": 0.0,
        "opponent_crosses_attempted": 0.0,
        "palmeiras_through_balls": 0.0,
        "opponent_through_balls": 0.0,
        "palmeiras_recoveries": 0.0,
        "opponent_recoveries": 0.0,
        "palmeiras_interceptions": 0.0,
        "opponent_interceptions": 0.0,
        "palmeiras_tackles_won_pct": 0.0,
        "opponent_tackles_won_pct": 0.0,
        "palmeiras_aerial_won_pct": 50.0,
        "opponent_aerial_won_pct": 50.0,
        "palmeiras_ground_won_pct": 50.0,
        "opponent_ground_won_pct": 50.0,
        "palmeiras_goals_prevented": 0.0,
        "opponent_goals_prevented": 0.0,
        "big_chances_palmeiras": 0.0,
        "big_chances_opponent": 0.0,
        "has_advanced_stats": False
    }

    if not stats_json or "statistics" not in stats_json or not stats_json["statistics"]:
        return res

    res["has_advanced_stats"] = True
    all_stats = stats_json["statistics"][0]
    
    # Mapear todos os itens de estatística
    raw_dict = {}
    for grp in all_stats.get("groups", []):
        for item in grp.get("statisticsItems", []):
            name = item.get("name")
            h_val = item.get("home")
            a_val = item.get("away")
            raw_dict[name] = {"home": h_val, "away": a_val}

    def get_team_vals(item_name: str):
        data = raw_dict.get(item_name, {})
        h = data.get("home")
        a = data.get("away")
        pal = h if is_palmeiras_home else a
        opp = a if is_palmeiras_home else h
        return pal, opp

    # 1. Posse de Bola
    p_poss, o_poss = get_team_vals("Ball possession")
    res["palmeiras_possession"] = _parse_val(p_poss) if p_poss else 50.0
    res["opponent_possession"] = _parse_val(o_poss) if o_poss else 50.0

    # 2. Toques na área (Touches in penalty area)
    p_tb, o_tb = get_team_vals("Touches in penalty area")
    res["palmeiras_touches_in_box"] = _parse_val(p_tb)
    res["opponent_touches_in_box"] = _parse_val(o_tb)

    # 3. Entradas no terço final (Final third entries)
    p_fe, o_fe = get_team_vals("Final third entries")
    pal_fe_val = _parse_val(p_fe)
    opp_fe_val = _parse_val(o_fe)
    res["palmeiras_final_third_entries"] = pal_fe_val
    res["opponent_final_third_entries"] = opp_fe_val

    # 4. Field Tilt (% das entradas no terço final)
    total_fe = pal_fe_val + opp_fe_val
    if total_fe > 0:
        res["field_tilt"] = round((pal_fe_val / total_fe) * 100.0, 1)
    else:
        res["field_tilt"] = 50.0

    # 5. Cruzamentos (Crosses)
    p_cr, o_cr = get_team_vals("Crosses")
    if p_cr and "/" in str(p_cr):
        try:
            parts = str(p_cr).split("/")
            res["palmeiras_crosses_attempted"] = _parse_val(parts[1].split()[0])
            res["palmeiras_crosses_acc_pct"] = _parse_val(p_cr)
        except Exception:
            pass
    if o_cr and "/" in str(o_cr):
        try:
            parts = str(o_cr).split("/")
            res["opponent_crosses_attempted"] = _parse_val(parts[1].split()[0])
        except Exception:
            pass

    # 6. Bolas Enfiadas / Passes em Profundidade (Through balls)
    p_thr, o_thr = get_team_vals("Through balls")
    res["palmeiras_through_balls"] = _parse_val(p_thr)
    res["opponent_through_balls"] = _parse_val(o_thr)

    # 7. Recuperações (Recoveries)
    p_rec, o_rec = get_team_vals("Recoveries")
    res["palmeiras_recoveries"] = _parse_val(p_rec)
    res["opponent_recoveries"] = _parse_val(o_rec)

    # 8. Interceptações (Interceptions)
    p_int, o_int = get_team_vals("Interceptions")
    res["palmeiras_interceptions"] = _parse_val(p_int)
    res["opponent_interceptions"] = _parse_val(o_int)

    # 9. Duelos no Chão e Aéreos
    p_ad, o_ad = get_team_vals("Aerial duels")
    res["palmeiras_aerial_won_pct"] = _parse_val(p_ad)
    res["opponent_aerial_won_pct"] = _parse_val(o_ad)

    p_gd, o_gd = get_team_vals("Ground duels")
    res["palmeiras_ground_won_pct"] = _parse_val(p_gd)
    res["opponent_ground_won_pct"] = _parse_val(o_gd)

    # 10. Gols Evitados pelo Goleiro (Goals prevented)
    p_gp, o_gp = get_team_vals("Goals prevented")
    res["palmeiras_goals_prevented"] = _parse_val(p_gp)
    res["opponent_goals_prevented"] = _parse_val(o_gp)

    # 11. Grandes Chances (Big chances)
    p_bc, o_bc = get_team_vals("Big chances")
    res["big_chances_palmeiras"] = _parse_val(p_bc)
    res["big_chances_opponent"] = _parse_val(o_bc)

    return res

def parse_match_lineups(lineups_json: Optional[Dict[str, Any]], is_palmeiras_home: bool) -> Dict[str, str]:
    """Extrai formações táticas do Palmeiras e do adversário."""
    res = {
        "palmeiras_formation": "Não informada",
        "opponent_formation": "Não informada"
    }
    if not lineups_json:
        return res

    home_form = lineups_json.get("home", {}).get("formation", "")
    away_form = lineups_json.get("away", {}).get("formation", "")

    if is_palmeiras_home:
        res["palmeiras_formation"] = home_form or "4-2-3-1"
        res["opponent_formation"] = away_form or "Não informada"
    else:
        res["palmeiras_formation"] = away_form or "4-2-3-1"
        res["opponent_formation"] = home_form or "Não informada"

    return res
