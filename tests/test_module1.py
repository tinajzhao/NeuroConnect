import pytest
import pandas as pd
import numpy as np
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), 'synthetic_data.csv')

@pytest.fixture
def data():
    if not os.path.exists(DATA_FILE):
        pytest.fail(f"Data file not found: {DATA_FILE}. Please run generate_data.py first.")
    return pd.read_csv(DATA_FILE, header=0, dtype={'LONIUID': str})

def test_examdate_format(data):
    """Verify EXAMDATE is a valid date string."""
    # Fail the test if date format is invalid
    try:
        pd.to_datetime(data['EXAMDATE'], format='%Y-%m-%d', errors='raise')
    except ValueError as e:
        pytest.fail(f"EXAMDATE contains invalid formats: {e}")

def test_status_complete(data):
    """Verify STATUS is strictly 'Complete'."""
    invalid_status = data[data['STATUS'] != 'Complete']
    assert invalid_status.empty, f"Found {len(invalid_status)} rows where STATUS is not 'Complete', {invalid_status}"

def test_loniuid_length(data):
    """Verify LONIUID is strictly 6 characters long."""
    # Check string length
    lengths = data['LONIUID'].str.len()
    invalid_rows = data.index[lengths != 6].to_list()
    if invalid_rows:
        pytest.fail(f"Found {len(invalid_rows)} rows where LONIUID is not 6 characters long: {invalid_rows}")

def test_ad_cst_values_validity(data):
    """Verify AD_CST_L and AD_CST_R are within expected statistical ranges (not abnormally large/small)."""
    # Means and STDs from sample data
    params = {
        'AD_CST_L': {'mean': 0.001307, 'std': 0.00018663},
        'AD_CST_R': {'mean': 0.0012545, 'std': 0.000167566}
    }

    for col, stat in params.items():
        values = data[col]
        
        # Sanity Check: Values should be positive
        assert (values > 0).all(), f"{col} contains non-positive values"
        
        # Outlier Check: Verify values are within 5 standard deviations
        z_scores = np.abs((values - stat['mean']) / stat['std'])
        outliers = z_scores > 5
        assert not outliers.any(), f"{col} contains abnormally extreme values (> 5 sigma)"

        # Distribution Check: The sample mean should be relatively close to the population mean
        assert np.isclose(values.mean(), stat['mean'], rtol=0.1), f"{col} mean deviates significantly from expected"