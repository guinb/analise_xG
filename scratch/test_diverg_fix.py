import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Test Divergência data
players = ["José Manuel López", "Gustavo Gómez", "Mauricio", "Allan", "Jhon Arias", "Vitor Roque", "Murilo", "Andreas Pereira"]
diff_b = [3.15, 1.01, 0.08, 2.22, 1.34, 1.31, 0.01, -0.49]
diff_t = [1.10, -0.01, 1.72, -0.45, 0.08, -0.81, 0.03, -0.62]

eff_candidates = pd.DataFrame({
    "player_name": players,
    "diff_eff_b": diff_b,
    "diff_eff_t": diff_t
})

# Look at how we build go.Figure directly with two distinct traces instead of px.bar melt!
fig = go.Figure()
fig.add_trace(go.Bar(
    y=eff_candidates["player_name"],
    x=eff_candidates["diff_eff_b"],
    name="Base (1º Turno)",
    orientation="h",
    marker_color="#00BFFF",
    text=eff_candidates["diff_eff_b"].apply(lambda v: f"{v:+.2f}"),
    textposition="outside"
))
fig.add_trace(go.Bar(
    y=eff_candidates["player_name"],
    x=eff_candidates["diff_eff_t"],
    name="Alvo (2º Turno)",
    orientation="h",
    marker_color="#00FF87",
    text=eff_candidates["diff_eff_t"].apply(lambda v: f"{v:+.2f}"),
    textposition="outside"
))
fig.update_layout(barmode="group")
print("Explicit traces guarantee 100% perfect row alignment!")
