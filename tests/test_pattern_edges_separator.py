import sys

import numpy as np
import pandas as pd

sys.path.append(".")
import src.neuroconnect.app_shiny_neuroconnect as app

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
