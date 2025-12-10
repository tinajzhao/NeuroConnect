"""
Tests for Brain Visualization Manager
"""
import sys
import plotly.graph_objects as go
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import neuroconnect.app_shiny_neuroconnect as app

# Unit tests (edge cases)
def test_normalize_columns_missing_required_raises():
    """
    author: Carlos Pineda
    reviewer: Tina
    category: edge case test
    description: Test that normalize_columns raises ValueError when required columns are missing.
    """
    df = pd.DataFrame({"x":[1,2,3]})
    with pytest.raises(ValueError):
        app.normalize_columns(df)

def test_points_within_ellipsoid():
    """
    author: Carlos Pineda
    reviewer: Tina
    category: edge case test
    description: Test that points are sampled within the defined ellipsoid.
    """
    pts = app.sample_points_in_ellipsoid(
        n=200, rx=app.RX, ry=app.RY, rz=app.RZ, seed=42
    )
    assert pts.shape == (200, 3)
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    lhs = (x**2) / (app.RX**2) + (y**2) / (app.RY**2) + (z**2) / (app.RZ**2)
    assert np.all(lhs <= 1.0 + 1e-9)

def test_numpy_ptp_function_usage():
    """
    author: Carlos Pineda
    reviewer: Tina
    category: edge case test
    description: Test that the numpy.ptp function is used correctly.
    """
    arr = np.array([1.0, 2.0, 3.5, -4.0])
    rng = np.ptp(arr)
    assert np.isclose(rng, arr.max() - arr.min())

# Unit tests (Patterns)

def test_edges_to_plotly_lines_pattern_and_values():
    """
    author: Carlos Pineda
    reviewer: Tina
    category: Pattern test
    description: Test that edges_to_plotly_lines produces correct pattern with None separators and correct values
    """

    df = pd.DataFrame(
        [
            {"x": 0.0, "y": 0.0, "z": 0.0, "id": "n0"},
            {"x": 5.0, "y": 0.0, "z": 0.0, "id": "n1"},
            {"x": 9.0, "y": 0.0, "z": 0.0, "id": "n2"},
        ]
    )
    edges = [(0, 1), (1, 2)]
    xs, ys, zs = app.edges_to_plotly_lines(df, edges)

    assert len(xs) == len(ys) == len(zs)
    assert len(xs) % 3 == 0

    for k in range(2):
        i = 3 * k
        assert xs[i + 2] is None
        assert ys[i + 2] is None
        assert zs[i + 2] is None

    assert np.isclose(xs[0], df.loc[0, "x"]) and np.isclose(xs[1], df.loc[1, "x"])
    assert np.isclose(xs[3], df.loc[1, "x"]) and np.isclose(xs[4], df.loc[2, "x"])

#Smoke tests

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

#Unit test (one-shot integration test)

def test_one_shot_single_point_has_no_edges():
    """
    author: Carlos Pineda
    reviewer: Tina
    category: one-shot test
    description: Test that a single point results in no edges being created.
    """
    df = pd.DataFrame([{"x":0.0,"y":0.0,"z":0.0,"id":"only"}])
    e_knn = app.build_edges_knn(df, k=4)
    e_dist = app.build_edges_distance(df, max_dist=25.0)
    assert e_knn == []
    assert e_dist == []

    xs, ys, zs = app.edges_to_plotly_lines(df, e_knn)
    assert xs == [] and ys == [] and zs == []
