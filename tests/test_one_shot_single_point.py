# tests/test_one_shot_single_point.py
import pandas as pd
import neuroconnect_app as appmod  # hypothetical module name

def test_one_shot_single_point_has_no_edges():
    """
    author: Carlos Pineda
    reviewer: Tina
    category: one shot test
    description: Test that a single point does not produce edges
    """
    df = pd.DataFrame([{"x": 0.0, "y": 0.0, "z": 0.0, "id": "only"}])
    # Distance builders should yield no edges
    e_knn = appmod.build_edges_knn(df, k=4)
    e_dist = appmod.build_edges_distance(df, max_dist=25.0)
    assert e_knn == []
    assert e_dist == []

    xs, ys, zs = appmod.edges_to_plotly_lines(df, e_knn)
    assert xs == [] and ys == [] and zs == []
