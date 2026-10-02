from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

def draw_mpl_pitch(formation_str, players=None):
    pitch = VerticalPitch(
        pitch_type="custom",
        pitch_length=105,
        pitch_width=68,
        half=False,
        pitch_color="#122416",
        line_color="#4A7552",
        linewidth=2,
        goal_type="box"
    )
    fig, ax = pitch.draw(figsize=(7, 9))
    fig.patch.set_facecolor("#0F172A")

    # Coordenadas em VerticalPitch:
    # X vai de 0 (gol de baixo / goleiro) a 105 (gol de cima / ataque)
    # Y vai de 0 a 68 (largura do campo, 34 é o centro)
    try:
        lines = [int(x) for x in str(formation_str).split('-')]
    except:
        lines = [4, 4, 2]
    
    # Goleiro
    coords = [(8, 34)]
    n_lines = len(lines)
    x_positions = [24 + i * (68 / max(1, n_lines - 1)) for i in range(n_lines)]

    for idx, (count, x_val) in enumerate(zip(lines, x_positions)):
        if count == 1:
            ys = [34]
        elif count == 2:
            ys = [24, 44]
        elif count == 3:
            ys = [18, 34, 50] if idx == 0 else [12, 34, 56]
        elif count == 4:
            ys = [10, 26, 42, 58]
        elif count == 5:
            ys = [8, 21, 34, 47, 60]
        else:
            ys = [10 + j * (48 / (count - 1)) for j in range(count)]
        for y_val in ys:
            coords.append((x_val, y_val))

    xs = [c[0] for c in coords[:11]]
    ys = [c[1] for c in coords[:11]]

    # Plotar jogadores
    pitch.scatter(xs, ys, s=480, color="#00FF87", edgecolors="#FFFFFF", linewidth=2.5, zorder=3, ax=ax)

    # Plotar textos dos jogadores
    for i, (x, y) in enumerate(zip(xs, ys)):
        if players and i < len(players):
            p = players[i]
            shirt = str(p.get("shirtNumber", ""))
            name = p.get("name", "").split()[-1]
            ax.text(y, x, shirt, color="#0A1E11", fontsize=10, fontweight="bold", ha="center", va="center", zorder=4)
            ax.text(y, x - 4.5, name, color="#FFFFFF", fontsize=9, fontweight="bold", ha="center", va="top", zorder=4,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="#1E293B", edgecolor="none", alpha=0.85))
        else:
            role_labels = ["GOL", "LAT/ZAG", "ZAG", "ZAG", "LAT/ZAG", "VOL", "VOL", "MEI", "MEI", "MEI", "ATA"]
            lbl = role_labels[i] if i < len(role_labels) else "JOG"
            ax.text(y, x - 4.5, lbl, color="#FFFFFF", fontsize=8.5, fontweight="bold", ha="center", va="top", zorder=4,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="#1E293B", edgecolor="none", alpha=0.85))

    plt.tight_layout()
    fig.savefig("scratch/test_pitch_out.png", dpi=100, facecolor=fig.get_facecolor())
    print("Pitch saved successfully to scratch/test_pitch_out.png!")

draw_mpl_pitch("4-2-3-1", [{"name": "Weverton", "shirtNumber": 21}, {"name": "Mayke", "shirtNumber": 12}])
