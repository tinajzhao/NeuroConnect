import pandas as pd
import numpy as np
import pytest
from src.neuroconnect.data_prep import (
    calc_group_diff,
    clean_data,
    compute_summary_statistics,
    format_output,
    load_data,
)

# Fixtures for data setup
@pytest.fixture
def mock_data_folder(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    
    # Diagnosis CSV creation
    diag_data = {
        'LONIUID': ['100', '101', '102', '103', '104'],
        'Group': ['AD', 'CN', 'AD', 'MCI', 'CN'], # MCI should be filtered out
        'EXAMDATE': ['2023-01-01'] * 5
    }
    pd.DataFrame(diag_data).to_csv(d / "diagnosis.csv", index=False)
    
    # DTI CSV creation
    dti_data = {
        'LONIUID': ['100', '101', '102', '103', '105'], # 105 has no diagnosis
        'Tract1': [0.5, 0.6, 0.55, 0.7, 0.9],
        'Tract2': [0.1, 0.2, 0.15, 0.3, 0.4]
    }
    pd.DataFrame(dti_data).to_csv(d / "DTI.csv", index=False)
    return str(d)

# Smoke Test
def test_full_pipeline_smoke(mock_data_folder):
    """
    author: Hongyu
    reviewer: Kenny
    category: Smoke Test

    Purpose: Verify that the full pipeline runs from loading to formatting without errors.
    """
    # Load
    diag, dti = load_data(mock_data_folder)
    assert not diag.empty
    assert not dti.empty
    
    # Clean
    cleaned = clean_data(diag, dti)
    # Expecting IDs 100 (AD), 101 (CN), 102 (AD). 
    # 103 is MCI (filtered out), 104 is in diag but not DTI, 105 in DTI but not diag.
    assert not cleaned.empty
    assert len(cleaned) == 3 
    assert 'MCI' not in cleaned['Group'].values
    
    # Statistics
    summary = compute_summary_statistics(cleaned)
    assert not summary.empty
    assert 'Group' in summary.columns
    assert len(summary) == 2 # AD and CN
    
    # Output
    output = format_output(summary)
    assert isinstance(output, list)
    assert len(output) == 2
    assert 'Group' in output[0]

# One-Shot Test
def test_compute_summary_statistics_one_shot():
    """
    author: Hongyu
    reviewer: Kenny
    category: One-Shot Test

    Purpose: Verify that compute_summary_statistics produces the exact expected mean values
    """
    input_df = pd.DataFrame({
        'LONIUID': ['1', '2', '3', '4'],
        'Group': ['AD', 'AD', 'CN', 'CN'],
        'TractA': [1.0, 2.0, 3.0, 4.0], # Mean AD=1.5, CN=3.5
        'TractB': [10.0, 20.0, 30.0, 40.0], # Mean AD=15.0, CN=35.0
        'Metadata': ['x', 'y', 'z', 'w'] # Should be ignored
    })
    
    result = compute_summary_statistics(input_df)
    
    # Check AD values
    ad_row = result[result['Group'] == 'AD'].iloc[0]
    assert np.isclose(ad_row['TractA'], 1.5)
    assert np.isclose(ad_row['TractB'], 15.0)
    
    # Check CN values
    cn_row = result[result['Group'] == 'CN'].iloc[0]
    assert np.isclose(cn_row['TractA'], 3.5)
    assert np.isclose(cn_row['TractB'], 35.0)

# Edge Test
def test_clean_data_no_matches_edge():
    """
    author: Hongyu
    reviewer: Kenny
    category: Edge Test

    Purpose: check if function returns an empty dataframe if there are no matches between the diagnosis and DTI data.
    """
    diag = pd.DataFrame({'LONIUID': ['1'], 'Group': ['AD']})
    dti = pd.DataFrame({'LONIUID': ['2'], 'Tract1': [0.5]})
    
    cleaned = clean_data(diag, dti)
    assert cleaned.empty
    
    summary = compute_summary_statistics(cleaned)
    assert summary.empty
    
    output = format_output(summary)
    assert output == []

# Pattern Test
def test_summary_stats_pattern_invariance():
    """
    author: Hongyu
    reviewer: Kenny
    category: Pattern Test

    Purpose: Verify that duplicating the dataset should not change the mean values.
    """
    # Create random synthetic data
    np.random.seed(42)
    df = pd.DataFrame({
        'LONIUID': [str(i) for i in range(10)],
        'Group': ['AD']*5 + ['CN']*5,
        'TractX': np.random.rand(10),
        'TractY': np.random.rand(10) * 100
    })
    
    # Double the data by concatenating it with itself
    df_doubled = pd.concat([df, df], ignore_index=True)
    
    stats_original = compute_summary_statistics(df)
    stats_doubled = compute_summary_statistics(df_doubled)
    
    # Sort by group to ensure alignment for comparison
    stats_original = stats_original.sort_values('Group').reset_index(drop=True)
    stats_doubled = stats_doubled.sort_values('Group').reset_index(drop=True)
    
    # Check if dataframes are equal (within float tolerance)
    pd.testing.assert_frame_equal(stats_original, stats_doubled)
    

# Tests for Calculating Group Differences
def test_calc_group_diff_smoke():
    """
    author: Kenny
    reviewer: Hongyu
    category: smoke test
    justification: check if function runs
    """
    test = pd.DataFrame({
        "PTID": [1, 2, 3, 4],
        "diagnosis": ["AD", "AD", "CN", "CN"],
        "feature1": [1, 2, 3, 4],
        "feature2": [5, 5, 5, 5],
    })
    test_fa_diff = calc_group_diff(test)
    assert test_fa_diff is not None

def test_calc_group_diff_oneshot():
    """
    author: Kenny
    reviewer: Hongyu
    category: one-shot test
    justification: check if function outputs expected result
    """
    test = pd.DataFrame({
        "PTID": [1, 2, 3, 4, 5, 6],
        "diagnosis": ["AD", "AD", "AD", "CN", "CN", "CN"],
        "feature1": [20, 22, 24, 10, 12, 14],  # AD mean: 22, CN mean: 12, AD-CN: 10
        "feature2": [15, 17, 19, 5, 7, 9],     # AD mean: 17, CN mean: 7, AD-CN: 10
    })
    
    expected = np.array([10.0, 10.0])
    result = calc_group_diff(test)
    
    np.testing.assert_allclose(result, expected)

def test_calc_group_diff_edge():
    """
    author: Kenny
    reviewer: Hongyu
    category: edge test
    justification: check if function handles error for invalid difference_type input
    """
    test = pd.DataFrame({
        "PTID": [1, 2, 3, 4],
        "diagnosis": ["AD", "AD", "CN", "CN"],
        "feature1": [1, 2, 3, 4],
        "feature2": [5, 5, 5, 5],
    })
    with pytest.raises(ValueError, match = "difference_type must be one of"):
        calc_group_diff(test, "number")


def test_calc_group_diff_pattern():
    """
    author: Kenny
    reviewer: Hongyu
    category: pattern test
    justification: check if output for groups with identical values is as expected
    """
    test = pd.DataFrame({
        "PTID": [1, 2, 3, 4],
        "diagnosis": ["AD", "AD", "CN", "CN"],
        "feature1": [10, 10, 10, 10],
        "feature2": [5, 5, 5, 5],
    })
    
    expected = np.array([0.0, 0.0])
    result = calc_group_diff(test)
    
    np.testing.assert_allclose(result, expected)
