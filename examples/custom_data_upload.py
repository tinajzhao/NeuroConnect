"""
Example 2: Custom DTI Data Upload
==================================

This example shows how to prepare your own DTI data for NeuroConnect.

Use this example when you have:
- Your own DTI metrics from the JHU ICBM-DTI-81 atlas
- Data in a different format (e.g., raw ADNI downloads)
- Multiple subjects you want to process into group-level summaries

This script demonstrates:
1. Loading custom DTI data
2. Formatting tract names to match JHU conventions
3. Calculating group-level statistics
4. Merging with pre-extracted coordinates
5. Preparing final data for the Shiny app
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path for importing neuroconnect modules
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from neuroconnect.data_prep import load_data, clean_data, compute_summary_statistics
except ImportError:
    print("Warning: Could not import neuroconnect modules. Using standalone functions.")
    print("Make sure you've installed the package: pip install -e .")


def simulate_custom_dti_data():
    """
    Simulate custom DTI data in a common format.
    
    This represents the typical format you might have from your own analysis:
    - One row per subject
    - Columns for subject ID, diagnosis, and FA values for each tract
    
    Returns
    -------
    pd.DataFrame
        Simulated subject-level DTI data
    """
    np.random.seed(123)
    
    # JHU tract names (subset for demonstration)
    tract_names = [
        'ATR_L', 'ATR_R', 'CST_L', 'CST_R', 'CGC_L', 'CGC_R',
        'FX_MAJOR', 'IFO_L', 'IFO_R', 'ILF_L', 'ILF_R',
        'SLF_L', 'SLF_R', 'UNC_L', 'UNC_R', 'GCC', 'SCC'
    ]
    
    # Simulate 30 subjects (15 CN, 15 AD)
    n_subjects = 30
    subjects = []
    
    for i in range(n_subjects):
        diagnosis = 'CN' if i < 15 else 'AD'
        
        # CN subjects have higher FA values
        if diagnosis == 'CN':
            fa_values = np.random.normal(0.50, 0.04, len(tract_names))
        else:
            fa_values = np.random.normal(0.42, 0.05, len(tract_names))
        
        # Clip to realistic range
        fa_values = np.clip(fa_values, 0.1, 0.9)
        
        # Create subject record
        subject_data = {
            'LONIUID': f'S{i+1:04d}',
            'diagnosis': diagnosis
        }
        
        # Add FA value for each tract
        for tract, fa in zip(tract_names, fa_values):
            subject_data[tract] = fa
        
        subjects.append(subject_data)
    
    df = pd.DataFrame(subjects)
    print(f"Simulated data for {n_subjects} subjects")
    print(f"  - {len(df[df['diagnosis']=='CN'])} CN subjects")
    print(f"  - {len(df[df['diagnosis']=='AD'])} AD subjects")
    print(f"  - {len(tract_names)} tracts per subject")
    
    return df


def calculate_group_means(subject_df):
    """
    Calculate mean FA values for each tract by diagnostic group.
    
    Parameters
    ----------
    subject_df : pd.DataFrame
        Subject-level data with FA values
        
    Returns
    -------
    pd.DataFrame
        Group-level means in long format
    """
    # Identify tract columns (exclude metadata)
    metadata_cols = ['LONIUID', 'diagnosis']
    tract_cols = [col for col in subject_df.columns if col not in metadata_cols]
    
    # Calculate group means
    group_means = subject_df.groupby('diagnosis')[tract_cols].mean()
    
    # Convert from wide to long format
    long_format = []
    for diagnosis in group_means.index:
        for tract in tract_cols:
            long_format.append({
                'tract_id': tract,
                'diagnosis': diagnosis,
                'metric_value': group_means.loc[diagnosis, tract]
            })
    
    result = pd.DataFrame(long_format)
    print(f"Calculated group means: {len(result)} tract-group combinations")
    return result


def load_jhu_coordinates():
    """
    Load pre-extracted JHU coordinates.
    
    Returns
    -------
    pd.DataFrame
        Tract coordinates
    """
    coord_file = Path(__file__).parent.parent / 'data' / 'jhu_coordinates.csv'
    
    if not coord_file.exists():
        raise FileNotFoundError(
            f"Coordinates file not found: {coord_file}\n"
            "Run from project root or check data/ directory."
        )
    
    coords = pd.read_csv(coord_file)
    print(f"Loaded coordinates for {len(coords)} tracts")
    return coords


def match_tract_names(dti_df, coords_df):
    """
    Verify that tract names in DTI data match JHU coordinate names.
    
    Parameters
    ----------
    dti_df : pd.DataFrame
        DTI data with tract_id column
    coords_df : pd.DataFrame
        Coordinate data with roi column
        
    Returns
    -------
    tuple
        (matched_tracts, missing_tracts)
    """
    dti_tracts = set(dti_df['tract_id'].unique())
    coord_tracts = set(coords_df['roi'].unique())
    
    matched = dti_tracts & coord_tracts
    missing = dti_tracts - coord_tracts
    
    print(f"Matched: {len(matched)} tracts")
    if missing:
        print(f"Missing coordinates for: {missing}")
        print(f"   (These tracts will be excluded from visualization)")
    
    return matched, missing


def prepare_visualization_data(dti_df, coords_df):
    """
    Merge DTI metrics with coordinates for visualization.
    
    Parameters
    ----------
    dti_df : pd.DataFrame
        DTI group means (tract_id, diagnosis, metric_value)
    coords_df : pd.DataFrame
        Tract coordinates (roi, start_x/y/z, end_x/y/z)
        
    Returns
    -------
    pd.DataFrame
        Complete visualization-ready data
    """
    # Merge on tract names
    viz_data = pd.merge(
        dti_df,
        coords_df,
        left_on='tract_id',
        right_on='roi',
        how='inner'
    )
    
    # Select and order columns for Shiny app
    final_cols = [
        'tract_id', 'start_x', 'start_y', 'start_z',
        'end_x', 'end_y', 'end_z', 'diagnosis', 'metric_value'
    ]
    
    viz_data = viz_data[final_cols]
    
    print(f"Prepared visualization data: {len(viz_data)} records")
    return viz_data


def validate_data_format(viz_data):
    """
    Check that data matches required format for NeuroConnect.
    
    Parameters
    ----------
    viz_data : pd.DataFrame
        Visualization data to validate
        
    Returns
    -------
    bool
        True if valid, raises error otherwise
    """
    required_cols = [
        'tract_id', 'start_x', 'start_y', 'start_z',
        'end_x', 'end_y', 'end_z', 'diagnosis', 'metric_value'
    ]
    
    # Check columns
    missing_cols = set(required_cols) - set(viz_data.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check for missing values
    if viz_data[required_cols].isnull().any().any():
        raise ValueError("Data contains missing values")
    
    # Check diagnosis values
    valid_diagnoses = {'CN', 'AD'}
    actual_diagnoses = set(viz_data['diagnosis'].unique())
    if not actual_diagnoses.issubset(valid_diagnoses):
        raise ValueError(f"Invalid diagnosis values: {actual_diagnoses - valid_diagnoses}")
    
    # Check metric_value range (FA should be 0-1)
    if (viz_data['metric_value'] < 0).any() or (viz_data['metric_value'] > 1).any():
        raise ValueError("metric_value (FA) should be between 0 and 1")
    
    print("✓ Data validation passed")
    return True


def save_for_upload(viz_data, output_file='custom_neuroconnect_data.csv'):
    """
    Save formatted data for Shiny app upload.
    
    Parameters
    ----------
    viz_data : pd.DataFrame
        Visualization-ready data
    output_file : str
        Output filename
    """
    output_path = Path(__file__).parent / output_file
    viz_data.to_csv(output_path, index=False)
    
    print(f"Saved to: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")


def main():
    """
    Main workflow for custom data preparation.
    """

    # Step 1: Load or simulate your custom DTI data 
    # Modify simulate_custom_dti_data() to load YOUR actual data
    subject_data = simulate_custom_dti_data() 
    
    # Step 2: Calculate group-level statistics
    group_means = calculate_group_means(subject_data)
    
    # Step 3: Load pre-extracted coordinates
    coords = load_jhu_coordinates()
    
    # Step 4: Verify tract name matching
    matched, missing = match_tract_names(group_means, coords)
    
    # Step 5: Merge data
    viz_data = prepare_visualization_data(group_means, coords)
    
    # Step 6: Validate format
    validate_data_format(viz_data)
    
    # Step 7: Save for upload
    save_for_upload(viz_data)
    
    # Summary
    print(f"Processed {len(subject_data)} subjects")
    print(f"Generated data for {len(viz_data['tract_id'].unique())} tracts")
    print(f"Both diagnostic groups: {sorted(viz_data['diagnosis'].unique())}")
    print()
    print("Next steps:")
    print("1. Review 'custom_neuroconnect_data.csv'")
    print("2. Upload to https://cpineda.shinyapps.io/neuroconnect/")
    print("3. Click 'Render / Update' to visualize your data")


if __name__ == '__main__':
    main()
