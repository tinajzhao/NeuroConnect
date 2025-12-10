import sys

import pandas as pd

sys.path.append(".")
import src.neuroconnect.app_shiny_neuroconnect as app

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
