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

