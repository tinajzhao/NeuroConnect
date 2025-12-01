
import numpy as np
import pandas as pd
import pytest
import sys

sys.path.append(".")
import app_shiny_neuroconnect as app

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
