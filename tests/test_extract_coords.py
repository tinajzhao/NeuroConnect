"""
Tests for Component 2: extract_coords
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path


# Import functions to test
from src.neuroconnect.extract_coords import (
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


def test_voxel_to_mni_smoke():
    """
    author: tinajzhao
    reviewer: CarlosPiant
    type: smoke test
    """
    affine = np.eye(4)
    voxel = np.array([10, 20, 30])
    result = voxel_to_mni(voxel, affine)
    assert result is not None
    return

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
    np.testing.assert_array_equal(result, expected)
    return

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
    np.testing.assert_array_almost_equal(result, expected)
    return

def test_voxel_to_mni_returns_3d():
    """
    author: tinajzhao
    reviewer: CarlosPiant
    type: edge test, result should be 3D (not 4D with homogeneous coordinate).
    """
    affine = np.eye(4)
    voxel = np.array([1, 2, 3])
    
    result = voxel_to_mni(voxel, affine)
    
    assert len(result) == 3, "Result should have exactly 3 elements"
    assert result.shape == (3,), "Result shape should be (3,)"
    return


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
    np.testing.assert_array_equal(result, expected)
    return

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
        np.testing.assert_array_equal(result, expected)
    
    return