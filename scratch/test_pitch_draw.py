import plotly.graph_objects as go

def draw_tactical_pitch(formation, players_list=None):
    fig = go.Figure()
    
    # Pitch dimensions 0 to 100
    # Field background
    fig.add_shape(type="rect", x0=2, y0=2, x1=98, y1=98, line=dict(color="#FFFFFF", width=2), fillcolor="#183624")
    # Halfway line
    fig.add_shape(type="line", x0=2, y0=50, x1=98, y1=50, line=dict(color="#FFFFFF", width=1.5))
    # Center circle
    fig.add_shape(type="circle", x0=38, y0=38, x1=62, y1=62, line=dict(color="#FFFFFF", width=1.5))
    fig.add_shape(type="circle", x0=49.2, y0=49.2, x1=50.8, y1=50.8, fillcolor="#FFFFFF", line_color="#FFFFFF")
    
    # Defense box (bottom)
    fig.add_shape(type="rect", x0=22, y0=2, x1=78, y1=22, line=dict(color="#FFFFFF", width=1.5))
    fig.add_shape(type="rect", x0=36, y0=2, x1=64, y1=9, line=dict(color="#FFFFFF", width=1.5))
    fig.add_shape(type="circle", x0=49.3, y0=13.3, x1=50.7, y1=14.7, fillcolor="#FFFFFF", line_color="#FFFFFF")
    
    # Attack box (top)
    fig.add_shape(type="rect", x0=22, y0=78, x1=78, y1=98, line=dict(color="#FFFFFF", width=1.5))
    fig.add_shape(type="rect", x0=36, y0=91, x1=64, y1=98, line=dict(color="#FFFFFF", width=1.5))
    fig.add_shape(type="circle", x0=49.3, y0=85.3, x1=50.7, y1=86.7, fillcolor="#FFFFFF", line_color="#FFFFFF")
    
    # Calculate player coords
    try:
        lines = [int(x) for x in str(formation).split('-')]
    except Exception:
        lines = [4, 4, 2]
    coords = [(50, 8)] # GK
    n_lines = len(lines)
    y_positions = [22 + i * (66 / max(1, n_lines - 1)) for i in range(n_lines)]
    
    for idx, (count, y) in enumerate(zip(lines, y_positions)):
        if count == 1:
            xs = [50]
        elif count == 2:
            xs = [36, 64]
        elif count == 3:
            xs = [26, 50, 74] if idx == 0 else [16, 50, 84]
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
        labels = [f"<b>{p.get('shirtNumber', '')}</b><br>{p.get('name', '')}" for p in players_list[:11]]
        hover_texts = [f"#{p.get('shirtNumber', '')} {p.get('name', '')} ({p.get('position', '')})" for p in players_list[:11]]
    else:
        role_labels = ["GOL", "LAT/ZAG", "ZAG", "ZAG", "LAT/ZAG", "VOL", "VOL", "MEI/PNT", "MEI", "MEI/PNT", "ATA"]
        labels = [f"<b>{role_labels[i] if i < len(role_labels) else 'JOG'}</b>" for i in range(len(coords[:11]))]
        hover_texts = labels
        
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="markers+text",
        marker=dict(size=24, color="#00FF87", line=dict(color="#0A1E11", width=2)),
        text=labels,
        textposition="top center",
        textfont=dict(color="#FFFFFF", size=10),
        hovertext=hover_texts,
        hoverinfo="text"
    ))
    
    fig.update_layout(
        template="plotly_dark",
        height=520,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 100]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 100], scaleanchor="x", scaleratio=1),
        showlegend=False
    )
    return fig

fig = draw_tactical_pitch("4-2-3-1")
print("Figure created successfully with shapes count:", len(fig.layout.shapes))
