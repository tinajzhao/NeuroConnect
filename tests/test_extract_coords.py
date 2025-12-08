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
