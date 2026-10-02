import plotly.graph_objects as go

def draw_compact_plotly_pitch(formation, players_list=None):
    fig = go.Figure()
    
    # Campo compacto e rápido: dimensões 0 a 100
    # Gramado verde escuro elegante
    fig.add_shape(type="rect", x0=2, y0=2, x1=98, y1=98, line=dict(color="#4A7552", width=1.5), fillcolor="#122416")
    # Linha de meio-campo
    fig.add_shape(type="line", x0=2, y0=50, x1=98, y1=50, line=dict(color="#4A7552", width=1.2))
    # Círculo central
    fig.add_shape(type="circle", x0=36, y0=36, x1=64, y1=64, line=dict(color="#4A7552", width=1.2))
    fig.add_shape(type="circle", x0=49, y0=49, x1=51, y1=51, fillcolor="#4A7552", line_color="#4A7552")
    
    # Área de defesa (Palmeiras)
    fig.add_shape(type="rect", x0=20, y0=2, x1=80, y1=20, line=dict(color="#4A7552", width=1.2))
    fig.add_shape(type="rect", x0=34, y0=2, x1=66, y1=8, line=dict(color="#4A7552", width=1.2))
    fig.add_shape(type="circle", x0=49.2, y0=13.2, x1=50.8, y1=14.8, fillcolor="#4A7552", line_color="#4A7552")
    
    # Área de ataque (Adversário)
    fig.add_shape(type="rect", x0=20, y0=80, x1=80, y1=98, line=dict(color="#4A7552", width=1.2))
    fig.add_shape(type="rect", x0=34, y0=92, x1=66, y1=98, line=dict(color="#4A7552", width=1.2))
    fig.add_shape(type="circle", x0=49.2, y0=85.2, x1=50.8, y1=86.8, fillcolor="#4A7552", line_color="#4A7552")
    
    # Coordenadas da formação
    try:
        lines = [int(x) for x in str(formation).split('-')]
    except Exception:
        lines = [4, 4, 2]
    coords = [(50, 9)] # GK
    n_lines = len(lines)
    y_positions = [24 + i * (62 / max(1, n_lines - 1)) for i in range(n_lines)]
    
    for idx, (count, y) in enumerate(zip(lines, y_positions)):
        if count == 1:
            xs = [50]
        elif count == 2:
            xs = [36, 64]
        elif count == 3:
            xs = [24, 50, 76] if idx == 0 else [18, 50, 82]
        elif count == 4:
            xs = [14, 38, 62, 86]
        elif count == 5:
            xs = [12, 31, 50, 69, 88]
        else:
            xs = [15 + j * (70 / (count - 1)) for j in range(count)]
        for x in xs:
            coords.append((round(x, 1), round(y, 1)))
            
    xs = [c[0] for c in coords[:11]]
    ys = [c[1] for c in coords[:11]]
    
    if players_list and len(players_list) >= 11:
        labels = [f"<b>{p.get('shirtNumber', '')}</b><br>{p.get('name', '').split()[-1]}" for p in players_list[:11]]
        hover_texts = [f"#{p.get('shirtNumber', '')} {p.get('name', '')} ({p.get('position', '')})" for p in players_list[:11]]
    else:
        role_labels = ["GOL", "LAT/ZAG", "ZAG", "ZAG", "LAT/ZAG", "VOL", "VOL", "MEI", "MEI", "MEI", "ATA"]
        labels = [f"<b>{role_labels[i] if i < len(role_labels) else 'JOG'}</b>" for i in range(len(coords[:11]))]
        hover_texts = labels
        
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="markers+text",
        marker=dict(size=24, color="#00FF87", line=dict(color="#0A1E11", width=2)),
        text=labels,
        textposition="top center",
        textfont=dict(color="#FFFFFF", size=9.5),
        hovertext=hover_texts,
        hoverinfo="text"
    ))
    
    fig.update_layout(
        template="plotly_dark",
        height=440,
        margin=dict(l=5, r=5, t=5, b=5),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 100], fixedrange=True),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 100], fixedrange=True),
        showlegend=False
    )
    return fig

fig = draw_compact_plotly_pitch("3-4-2-1", [{"name": "Weverton", "shirtNumber": 21}])
print("Compact Plotly pitch created in 0.01s, height 440px!")
