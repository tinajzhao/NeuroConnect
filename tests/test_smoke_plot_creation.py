# tests/test_smoke_plot_creation.py
import plotly.graph_objects as go
import numpy as np
import pandas as pd

import neuroconnect_app as appmod  # hypothetical module name

def test_smoke_minimal_figure_builds():
    """
    author: Carlos Pineda
    reviewer: Tina
    category: smoke test
    description: Smoke test to ensure minimal figure components build without error
    """
    # Surface traces (should return two Mesh3d traces)
    surface_traces = appmod.make_ellipsoid_traces(opacity=0.15)
    assert isinstance(surface_traces, list) and len(surface_traces) >= 2
    assert all(isinstance(t, go.Mesh3d) for t in surface_traces)

    # AOI mesh (one small sphere)
    aoi = appmod.make_aoi_mesh_trace(x=0, y=0, z=0, r=10, opacity=0.1)
    assert isinstance(aoi, go.Mesh3d)

    # Demo nodes (ensures helper works)
    df = appmod.generate_demo_nodes(n_nodes=20, seed=123, with_values=True)
    assert {"x", "y", "z", "id", "group"}.issubset(df.columns)

    # Compose a minimal figure (surface + AOI only; node plotting happens in the app)
    fig = go.Figure(surface_traces + [aoi])
    assert isinstance(fig, go.Figure)
    # Should have at least 3D scene in layout after update
    fig.update_layout(scene=dict(aspectmode="data"))
    assert "scene" in fig.layout
