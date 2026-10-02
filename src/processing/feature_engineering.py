"""
Engenharia de features para finalizações:
- Conversão e normalização de coordenadas para metros no campo padrão FIFA (105m x 68m).
- Cálculo trigonométrico da distância euclidiana ao gol e do ângulo de visão da trave (em graus).
- Classificação de faixas de perigo do xG.
- Mapeamento de situações de criação (Jogo Aberto, Bola Parada, Contra-Ataque, Pênalti).
- Cálculo de métricas de conversão (G - xG).
"""

import math
from typing import Dict, Any

PITCH_LENGTH_METERS = 105.0
PITCH_WIDTH_METERS = 68.0
GOAL_WIDTH_METERS = 7.32

def calculate_shot_geometry(x_pct: float, y_pct: float) -> Dict[str, float]:
    """
    No SofaScore:
    x_pct: porcentagem de distância da linha de fundo do gol adversário (0 a 100).
    y_pct: porcentagem lateral do campo (0 a 100, sendo 50 o centro do campo).
    """
    # Converter para metros
    x_meters = max(0.1, (x_pct / 100.0) * PITCH_LENGTH_METERS)
    y_meters = ((y_pct - 50.0) / 100.0) * PITCH_WIDTH_METERS
    
    # Distância Euclidiana ao centro do gol
    distance = math.sqrt(x_meters**2 + y_meters**2)
    
    # Ângulo de visão entre as duas traves (em graus)
    y_left_post = y_meters + (GOAL_WIDTH_METERS / 2.0)
    y_right_post = y_meters - (GOAL_WIDTH_METERS / 2.0)
    
    angle_rad = abs(math.atan2(y_left_post, x_meters) - math.atan2(y_right_post, x_meters))
    angle_deg = math.degrees(angle_rad)

    # Corredor tático (Centro, Direita, Esquerda)
    if y_meters > 10.0:
        corridor = "Lado Direito"
    elif y_meters < -10.0:
        corridor = "Lado Esquerdo"
    else:
        corridor = "Corredor Central"

    # Zona tática do campo (Pequena Área, Grande Área, Fora da Área)
    if distance <= 6.0:
        zone = "Pequena Área"
    elif x_meters <= 16.5 and abs(y_meters) <= 20.15:
        zone = "Grande Área"
    else:
        zone = "Fora da Área"

    # Faixa de distância
    if distance < 12.0:
        dist_band = "< 12m (Perto do Gol)"
    elif distance <= 18.0:
        dist_band = "12m - 18m (Grande Área)"
    elif distance <= 25.0:
        dist_band = "18m - 25m (Entrada da Área)"
    else:
        dist_band = "> 25m (Chute Longo)"
    
    return {
        "x_meters": round(x_meters, 2),
        "y_meters": round(y_meters, 2),
        "distance_meters": round(distance, 2),
        "angle_degrees": round(angle_deg, 2),
        "shot_corridor": corridor,
        "shot_zone": zone,
        "distance_band": dist_band
    }

def classify_xg_danger(xg: float) -> str:
    if xg >= 0.30:
        return "Alta (>=0.30)"
    elif xg >= 0.10:
        return "Média (0.10 a 0.29)"
    elif xg >= 0.04:
        return "Baixa (0.04 a 0.09)"
    else:
        return "Especulativa (<0.04)"

def normalize_situation(situation_raw: str) -> str:
    s = (situation_raw or "").lower()
    if s in ("regular", "assisted"):
        return "Jogo Aberto"
    elif "fast" in s or "counter" in s or "break" in s:
        return "Contra-Ataque"
    elif "corner" in s:
        return "Escanteio"
    elif "free" in s or "set" in s:
        return "Falta / Bola Parada"
    elif "penalty" in s:
        return "Pênalti"
    elif "throw" in s:
        return "Lateral"
    else:
        return "Jogo Aberto"

def normalize_body_part(body_part_raw: str) -> str:
    bp = (body_part_raw or "").lower()
    if "head" in bp:
        return "Cabeça"
    elif "right" in bp:
        return "Pé Direito"
    elif "left" in bp:
        return "Pé Esquerdo"
    else:
        return "Outros"

def normalize_shot_outcome(shot_type_raw: str) -> Dict[str, Any]:
    st = (shot_type_raw or "").lower()
    is_goal = (st == "goal")
    label_map = {
        "goal": "Gol",
        "save": "Defesa",
        "miss": "Para Fora",
        "block": "Bloqueado",
        "post": "Trave"
    }
    return {
        "outcome": label_map.get(st, "Outro"),
        "is_goal": is_goal
    }
