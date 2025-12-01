
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import sys

sys.path.append(".")
import app_shiny_neuroconnect as app

def test_smoke_minimal_figure_builds():
    """
    author: Carlos Pineda
    reviewer: Tina
    category: smoke test
    description: Test that minimal figure components can be created without errors.
    """
    surface_traces = app.make_ellipsoid_traces(opacity=0.15)
    assert isinstance(surface_traces, list) and len(surface_traces) >= 2
    assert all(isinstance(t, go.Mesh3d) for t in surface_traces)

    aoi = app.make_aoi_mesh_trace(x=0, y=0, z=0, r=10, opacity=0.1)
    assert isinstance(aoi, go.Mesh3d)

    df = app.generate_demo_nodes(n_nodes=20, seed=123, with_values=True)
    assert {"x","y","z","id","group"}.issubset(df.columns)

    fig = go.Figure(surface_traces + [aoi])
    fig.update_layout(scene=dict(aspectmode="data"))
    assert "scene" in fig.layout
