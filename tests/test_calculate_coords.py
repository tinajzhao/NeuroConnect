"""
Tests for Component 2: extract_coords; calculation part
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import functions from your script
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from neuroconnect.extract_coords import (
    get_tract_from_df,
    average_tract_coords,
    calculate_bcc,
    calculate_full_cc,
    calculate_composite_tracts,
    save_coordinates,
)


# Helper Functions for Composite Tracts

def test_get_tract_from_df_found():
    """
    type: one-shot test, retrieve an existing tract.
    """
    df = pd.DataFrame({
        'roi': ['CST_L', 'CST_R', 'CGC_L'],
        'start_x': [10, 20, 30],
        'start_y': [15, 25, 35],
    })
    
    result = get_tract_from_df(df, 'CST_R')
    
    assert result is not None, "Should find existing tract 'CST_R'"
    assert result['roi'] == 'CST_R', (
        f"Wrong tract returned: expected 'CST_R', got '{result['roi']}'"
    )
    assert result['start_x'] == 20, (
        f"Wrong start_x: expected 20, got {result['start_x']}"
    )
    assert result['start_y'] == 25, (
        f"Wrong start_y: expected 25, got {result['start_y']}"
    )


def test_get_tract_from_df_not_found():
    """
    type: edge test, return None for non-existent tract.
    """
    df = pd.DataFrame({
        'roi': ['CST_L', 'CST_R'],
        'start_x': [10, 20],
    })
    
    result = get_tract_from_df(df, 'MISSING')
    
    assert result is None, (
        "Should return None for non-existent tract, "
        f"but got {result}"
    )



def test_average_tract_coords_two_tracts():
    """
    type: one-shot test, average of two tracts with known values.
    """
    tract1 = pd.Series({
        'start_x': 10, 'start_y': 20, 'start_z': 30,
        'end_x': 40, 'end_y': 50, 'end_z': 60,
        'centroid_x': 25, 'centroid_y': 35, 'centroid_z': 45
    })
    tract2 = pd.Series({
        'start_x': 20, 'start_y': 30, 'start_z': 40,
        'end_x': 50, 'end_y': 60, 'end_z': 70,
        'centroid_x': 35, 'centroid_y': 45, 'centroid_z': 55
    })
    
    result = average_tract_coords(tract1, tract2)
    
    assert result['start_x'] == 15, (
        f"start_x average incorrect: expected 15, got {result['start_x']}"
    )
    assert result['start_y'] == 25, (
        f"start_y average incorrect: expected 25, got {result['start_y']}"
    )
    assert result['end_z'] == 65, (
        f"end_z average incorrect: expected 65, got {result['end_z']}"
    )
    assert result['centroid_x'] == 30, (
        f"centroid_x average incorrect: expected 30, got {result['centroid_x']}"
    )


def test_average_tract_coords_single_tract():
    """
    type: edge test, single tract should return same values.
    """
    tract = pd.Series({
        'start_x': 42, 'start_y': 43, 'start_z': 44,
        'end_x': 45, 'end_y': 46, 'end_z': 47,
        'centroid_x': 48, 'centroid_y': 49, 'centroid_z': 50
    })
    
    result = average_tract_coords(tract)
    
    assert result['start_x'] == 42, (
        f"Single tract: start_x should be unchanged (42), got {result['start_x']}"
    )
    assert result['end_z'] == 47, (
        f"Single tract: end_z should be unchanged (47), got {result['end_z']}"
    )
    assert result['centroid_z'] == 50, (
        f"Single tract: centroid_z should be unchanged (50), got {result['centroid_z']}"
    )



def test_calculate_bcc_midpoint():
    """
    type: one-shot test, BCC should be midpoint of GCC and SCC.
    
    The body of corpus callosum is anatomically defined as the
    midpoint between genu and splenium.
    """
    gcc = pd.Series({
        'start_y': 10, 'start_z': 20,
        'end_y': 30, 'end_z': 40,
        'centroid_y': 20, 'centroid_z': 30
    })
    scc = pd.Series({
        'start_y': 20, 'start_z': 30,
        'end_y': 40, 'end_z': 50,
        'centroid_y': 30, 'centroid_z': 40
    })
    
    result = calculate_bcc(gcc, scc)
    
    assert result['roi'] == 'BCC', (
        f"ROI name should be 'BCC', got '{result['roi']}'"
    )
    assert result['start_y'] == 15, (
        f"start_y midpoint incorrect: expected 15, got {result['start_y']}"
    )
    assert result['start_z'] == 25, (
        f"start_z midpoint incorrect: expected 25, got {result['start_z']}"
    )
    assert result['end_y'] == 35, (
        f"end_y midpoint incorrect: expected 35, got {result['end_y']}"
    )
    assert result['centroid_z'] == 35, (
        f"centroid_z midpoint incorrect: expected 35, got {result['centroid_z']}"
    )


def test_calculate_bcc_x_always_zero():
    """
    type: edge test, all x-coordinates should be 0 (midline structure).
    
    Corpus callosum is a midline structure and should have x=0
    to maintain anatomical accuracy.
    """
    gcc = pd.Series({
        'start_y': 100, 'start_z': 100,
        'end_y': 100, 'end_z': 100,
        'centroid_y': 100, 'centroid_z': 100
    })
    scc = pd.Series({
        'start_y': 200, 'start_z': 200,
        'end_y': 200, 'end_z': 200,
        'centroid_y': 200, 'centroid_z': 200
    })
    
    result = calculate_bcc(gcc, scc)
    
    assert result['start_x'] == 0, (
        f"BCC start_x should be 0 (midline), got {result['start_x']}"
    )
    assert result['end_x'] == 0, (
        f"BCC end_x should be 0 (midline), got {result['end_x']}"
    )
    assert result['centroid_x'] == 0, (
        f"BCC centroid_x should be 0 (midline), got {result['centroid_x']}"
    )


def test_calculate_full_cc_average():
    """
    type: one-shot test, full CC should be average of GCC, BCC, SCC.
    
    The full corpus callosum represents the entire structure
    as the average of its three parts.
    """
    gcc = pd.Series({
        'start_y': 10, 'start_z': 10,
        'end_y': 10, 'end_z': 10,
        'centroid_y': 10, 'centroid_z': 10
    })
    bcc = {
        'start_y': 20, 'start_z': 20,
        'end_y': 20, 'end_z': 20,
        'centroid_y': 20, 'centroid_z': 20
    }
    scc = pd.Series({
        'start_y': 30, 'start_z': 30,
        'end_y': 30, 'end_z': 30,
        'centroid_y': 30, 'centroid_z': 30
    })
    
    result = calculate_full_cc(gcc, bcc, scc)
    
    assert result['roi'] == 'CC', (
        f"ROI name should be 'CC', got '{result['roi']}'"
    )
    assert result['start_y'] == 20, (
        f"start_y average incorrect: expected 20 (avg of 10,20,30), got {result['start_y']}"
    )
    assert result['start_z'] == 20, (
        f"start_z average incorrect: expected 20, got {result['start_z']}"
    )
    assert result['centroid_z'] == 20, (
        f"centroid_z average incorrect: expected 20, got {result['centroid_z']}"
    )


def test_calculate_composite_tracts_smoke():
    """
    type: smoke test
    """
    # Create minimal DataFrame with required tracts
    base_df = pd.DataFrame({
        'roi': ['GCC', 'SCC', 'ALIC_L', 'ALIC_R'],
        'start_x': [0, 0, 10, -10],
        'start_y': [10, -10, 0, 0],
        'start_z': [10, 10, 5, 5],
        'end_x': [0, 0, 15, -15],
        'end_y': [20, -20, 10, 10],
        'end_z': [20, 20, 15, 15],
        'centroid_x': [0, 0, 12.5, -12.5],
        'centroid_y': [15, -15, 5, 5],
        'centroid_z': [15, 15, 10, 10],
    })
    
    result = calculate_composite_tracts(base_df)
    
    assert result is not None, "calculate_composite_tracts should return a result"
    assert isinstance(result, list), (
        f"Result should be list, got {type(result)}"
    )


def test_save_coordinates_creates_file():
    """
    type: edge test, function should create a CSV file.
    """
    base_df = pd.DataFrame({
        'roi': ['CST_L'],
        'start_x': [10], 'start_y': [20], 'start_z': [30],
        'end_x': [40], 'end_y': [50], 'end_z': [60],
        'centroid_x': [25], 'centroid_y': [35], 'centroid_z': [45],
    })
    composite_list = []
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = f.name
    
    try:
        save_coordinates(base_df, composite_list, temp_path)
        assert os.path.exists(temp_path), (
            f"CSV file should be created at {temp_path}"
        )
        
        # Verify file can be read
        loaded_df = pd.read_csv(temp_path)
        assert len(loaded_df) == 1, (
            f"Saved CSV should have 1 row, got {len(loaded_df)}"
        )
        assert loaded_df.iloc[0]['roi'] == 'CST_L', (
            f"Loaded data incorrect: expected 'CST_L', got '{loaded_df.iloc[0]['roi']}'"
        )
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_save_coordinates_combines_base_and_composite():
    """
    type: one-shot test, function should combine base and composite tracts.
    """
    base_df = pd.DataFrame({
        'roi': ['CST_L'],
        'start_x': [10], 'start_y': [20], 'start_z': [30],
        'end_x': [40], 'end_y': [50], 'end_z': [60],
        'centroid_x': [25], 'centroid_y': [35], 'centroid_z': [45],
    })
    composite_list = [{
        'roi': 'BCC',
        'start_x': 0, 'start_y': 15, 'start_z': 25,
        'end_x': 0, 'end_y': 35, 'end_z': 45,
        'centroid_x': 0, 'centroid_y': 25, 'centroid_z': 35,
    }]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = f.name
    
    try:
        result = save_coordinates(base_df, composite_list, temp_path)
        
        assert len(result) == 2, (
            f"Combined DataFrame should have 2 rows (1 base + 1 composite), "
            f"got {len(result)}"
        )
        assert result.iloc[0]['roi'] == 'CST_L', (
            f"First row should be 'CST_L', got '{result.iloc[0]['roi']}'"
        )
        assert result.iloc[1]['roi'] == 'BCC', (
            f"Second row should be 'BCC', got '{result.iloc[1]['roi']}'"
        )
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

