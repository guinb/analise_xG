def get_formation_coords(formation_str):
    try:
        lines = [int(x) for x in str(formation_str).split('-')]
    except Exception:
        lines = [4, 4, 2]
    coords = [(50, 8)] # GK
    n_lines = len(lines)
    y_positions = [22 + i * (66 / max(1, n_lines - 1)) for i in range(n_lines)]
    
    for idx, (count, y) in enumerate(zip(lines, y_positions)):
        if count == 1:
            xs = [50]
        elif count == 2:
            # Se for linha de 2 no meio ou ataque, posiciona no terço central
            xs = [36, 64]
        elif count == 3:
            # Linha de 3 zagueiros ou 3 meias
            if idx == 0: # 3 zagueiros
                xs = [26, 50, 74]
            else: # 3 meias ofensivos / pontas
                xs = [16, 50, 84]
        elif count == 4:
            # 4 defensores ou 4 meias
            xs = [14, 38, 62, 86]
        elif count == 5:
            xs = [12, 31, 50, 69, 88]
        else:
            xs = [15 + j * (70 / (count - 1)) for j in range(count)]
        for x in xs:
            coords.append((round(x, 1), round(y, 1)))
    return coords

for f in ["4-2-3-1", "3-4-2-1", "3-5-2", "4-4-2", "4-3-3", "4-1-3-2"]:
    c = get_formation_coords(f)
    print(f, f"Total players: {len(c)}", c)
