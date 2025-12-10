"""
Tests for tract coordinate extraction functions
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import functions to test
from neuroconnect.extract_coords import (
    find_atlas,
    voxel_to_mni,
    extract_tract_coords,
    extract_base_tracts,
    get_tract_from_df,
    average_tract_coords,
    calculate_bcc,
    calculate_full_cc,
    calculate_composite_tracts,
    save_coordinates,
)

# Tests for find_atlas
def test_find_atlas_smoke():
    """
    type: smoke test
    """
    try:
        result = find_atlas()
        assert result is not None, "find_atlas should return a path string"
        assert isinstance(result, str), f"Expected str, got {type(result)}"
    except FileNotFoundError:
        # Expected if atlas not installed - test passes
        pass


def test_find_atlas_returns_string():
    """
    type: edge test - if atlas is found, result should be a string path.
    """
    try:
        result = find_atlas()
        assert isinstance(result, str), (
            f"find_atlas should return str path, got {type(result)}"
        )
        assert len(result) > 0, "find_atlas should return non-empty path"
    except FileNotFoundError:
        # Expected if atlas not installed
        pass


def test_find_atlas_file_exists():
    """
    type: edge test - if find_atlas succeeds, the file should actually exist.
    """
    try:
        atlas_path = find_atlas()
        assert Path(atlas_path).exists(), (
            f"find_atlas returned path that doesn't exist: {atlas_path}"
        )
        assert Path(atlas_path).is_file(), (
            f"find_atlas returned path that isn't a file: {atlas_path}"
        )
    except FileNotFoundError:
        # Expected if atlas not installed
        pass


# Tests for voxel_to_mni
def test_voxel_to_mni_smoke():
    """
    author: tinajzhao
    reviewer: CarlosPiant
    type: smoke test
    """
    affine = np.eye(4)
    voxel = np.array([10, 20, 30])
    result = voxel_to_mni(voxel, affine)
    assert result is not None, "voxel_to_mni should return a result"


def test_voxel_to_mni_identity_matrix():
    """
    author: tinajzhao
    reviewer: CarlosPiant
    type: one-shot test, identity matrix should return same coordinates.
    """
    affine = np.eye(4)
    voxel = np.array([10, 20, 30])
    
    result = voxel_to_mni(voxel, affine)
    
    expected = np.array([10, 20, 30])
    np.testing.assert_array_equal(
        result, expected,
        err_msg="Identity matrix should preserve coordinates"
    )

def test_voxel_to_mni_translation():
    """
    author: tinajzhao
    reviewer: CarlosPiant
    type: one-shot test, test with translation matrix.
    Known case: 2mm voxels with origin at [-90, -126, -72].
    """
    affine = np.array([
        [2, 0, 0, -90],
        [0, 2, 0, -126],
        [0, 0, 2, -72],
        [0, 0, 0, 1]
    ])
    voxel = np.array([50, 60, 40])
    
    result = voxel_to_mni(voxel, affine)
    
    expected = np.array([10, -6, 8])  # 2*50-90, 2*60-126, 2*40-72
    np.testing.assert_array_almost_equal(
        result, expected,
        err_msg=f"Translation failed: expected {expected}, got {result}"
    )

def test_voxel_to_mni_returns_3d():
    """
    author: tinajzhao
    reviewer: CarlosPiant
    type: edge test, result should be 3D (not 4D with homogeneous coordinate).
    """
    affine = np.eye(4)
    voxel = np.array([1, 2, 3])
    
    result = voxel_to_mni(voxel, affine)
    
    assert len(result) == 3, (
        f"Result should have exactly 3 elements, got {len(result)}"
    )
    assert result.shape == (3,), (
        f"Result shape should be (3,), got {result.shape}"
    )


def test_voxel_to_mni_origin():
    """
    author: tinajzhao
    reviewer: CarlosPiant
    type: edge test, voxel [0, 0, 0] should map to affine translation.
    """
    affine = np.array([
        [1, 0, 0, -50],
        [0, 1, 0, -60],
        [0, 0, 1, -40],
        [0, 0, 0, 1]
    ])
    voxel = np.array([0, 0, 0])
    
    result = voxel_to_mni(voxel, affine)
    
    expected = np.array([-50, -60, -40])
    np.testing.assert_array_equal(
        result, expected,
        err_msg=f"Origin transformation failed: expected {expected}, got {result}"
    )

def test_voxel_to_mni_pattern_scaling():
    """
    author: tinajzhao
    reviewer: CarlosPiant
    type: pattern test, doubling voxel size should double MNI coordinates
    (when origin is at 0).
    """
    voxel = np.array([10, 20, 30])
    
    # Test with different voxel sizes
    for scale in [1, 2, 3, 5, 10]:
        affine = np.diag([scale, scale, scale, 1])
        result = voxel_to_mni(voxel, affine)
        expected = voxel * scale
        np.testing.assert_array_equal(
            result, expected,
            err_msg=(
                f"Scaling pattern failed at scale={scale}: "
                f"expected {expected}, got {result}"
            )
        )

# Tests for extract_tract_coords, extracting coordinates for a single tract
def test_extract_tract_coords_smoke():
    """
    type: smoke test.
    """
    # Create simple 3D atlas with one ROI
    atlas_data = np.zeros((10, 10, 10))
    atlas_data[4:6, 4:6, 4:6] = 1  # ROI 1 is a small cube
    atlas_affine = np.eye(4)
    
    result = extract_tract_coords(atlas_data, atlas_affine, 1)
    
    assert result is not None, "extract_tract_coords should return a result for valid ROI"
    assert 'start' in result, "Result should contain 'start' key"
    assert 'end' in result, "Result should contain 'end' key"
    assert 'centroid' in result, "Result should contain 'centroid' key"


def test_extract_tract_coords_empty_roi():
    """
    type: edge test, non-existent ROI should return None.
    """
    atlas_data = np.zeros((10, 10, 10))
    atlas_data[4:6, 4:6, 4:6] = 1  # Only ROI 1 exists
    atlas_affine = np.eye(4)
    
    result = extract_tract_coords(atlas_data, atlas_affine, 2)  # ROI 2 doesn't exist
    
    assert result is None, (
        "extract_tract_coords should return None for non-existent ROI, "
        f"but got {result}"
    )


def test_extract_tract_coords_returns_correct_keys():
    """
    type: edge test, result should have correct dictionary structure.
    """
    atlas_data = np.zeros((10, 10, 10))
    atlas_data[4:6, 4:6, 4:6] = 1
    atlas_affine = np.eye(4)
    
    result = extract_tract_coords(atlas_data, atlas_affine, 1)
    
    assert isinstance(result, dict), (
        f"Result should be dict, got {type(result)}"
    )
    
    required_keys = ['start', 'end', 'centroid']
    for key in required_keys:
        assert key in result, f"Result missing required key: {key}"
        assert len(result[key]) == 3, (
            f"Coordinate '{key}' should have 3 elements, got {len(result[key])}"
        )


def test_extract_tract_coords_single_voxel():
    """
    type: edge test, single voxel ROI should have start == end == centroid.
    """
    atlas_data = np.zeros((10, 10, 10))
    atlas_data[5, 5, 5] = 1  # Single voxel
    atlas_affine = np.eye(4)
    
    result = extract_tract_coords(atlas_data, atlas_affine, 1)
    
    # All three should be approximately the same location
    np.testing.assert_array_almost_equal(
        result['start'], result['end'],
        err_msg="Single voxel: start should equal end"
    )
    np.testing.assert_array_almost_equal(
        result['start'], result['centroid'],
        err_msg="Single voxel: start should equal centroid"
    )

# Tests for extract_base_tracts, loop extract_tract_coords through 48 base tracts
def test_extract_base_tracts_smoke():
    """
    type: smoke test
    """
    # Create simple atlas with a few ROIs
    atlas_data = np.zeros((10, 10, 10))
    atlas_data[2:4, 2:4, 2:4] = 1  # ROI 1
    atlas_data[6:8, 6:8, 6:8] = 2  # ROI 2
    atlas_affine = np.eye(4)
    
    result = extract_base_tracts(atlas_data, atlas_affine)
    
    assert result is not None, "extract_base_tracts should return a dataframe"
    assert isinstance(result, pd.DataFrame), (
        f"Result should be DataFrame, got {type(result)}"
    )


def test_extract_base_tracts_returns_dataframe():
    """
    type: edge test, esult should be a dataframe with correct columns.
    """
    atlas_data = np.zeros((10, 10, 10))
    atlas_data[2:4, 2:4, 2:4] = 1
    atlas_affine = np.eye(4)
    
    result = extract_base_tracts(atlas_data, atlas_affine)
    
    expected_columns = [
        'roi', 'start_x', 'start_y', 'start_z',
        'end_x', 'end_y', 'end_z',
        'centroid_x', 'centroid_y', 'centroid_z'
    ]
    
    for col in expected_columns:
        assert col in result.columns, (
            f"DataFrame missing expected column: {col}"
        )


def test_extract_base_tracts_empty_atlas():
    """
    type: edge test, empty atlas should return empty dataframe.
    """
    atlas_data = np.zeros((10, 10, 10))  # No ROIs
    atlas_affine = np.eye(4)
    
    result = extract_base_tracts(atlas_data, atlas_affine)
    
    assert len(result) == 0, (
        f"Empty atlas should produce empty DataFrame, got {len(result)} rows"
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

