"""
Example 2: Custom DTI Data Upload
==================================

This example shows how to prepare your own DTI data for NeuroConnect.

Use this example when you have:
- Your own DTI metrics from the JHU ICBM-DTI-81 atlas
- Data in ADNI format (diagnosis.csv + DTI.csv)
- Multiple subjects you want to process into group-level summaries

This script demonstrates the complete pipeline:
1. Loading diagnosis and DTI data (load_data)
2. Merging and cleaning data (clean_data)
3. Calculating group-level statistics (compute_summary_statistics)
4. Merging with pre-extracted coordinates
5. Preparing final data for the Shiny app

Note: Running this script will create diagnosis.csv and DTI.csv demo files
in the examples/ directory for demonstration purposes.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from neuroconnect.data_prep import clean_data, compute_summary_statistics, load_data


def simulate_adni_data(n_subjects=40):
    """
    Simulate ADNI-format data files for demonstration.
    
    Creates diagnosis.csv and DTI.csv in examples/ directory.
    In a real workflow, replace this with your actual ADNI files.
    
    Parameters
    ----------
    n_subjects : int
        Number of subjects to simulate
        
    Returns
    -------
    str
        Path to directory containing demo files
    """
    np.random.seed(123)

    # JHU tract names (subset for demo)
    tract_names = [
        'ATR_L', 'ATR_R', 'CST_L', 'CST_R', 'CGC_L', 'CGC_R',
        'FX_MAJOR', 'IFO_L', 'IFO_R', 'ILF_L', 'ILF_R',
        'SLF_L', 'SLF_R', 'UNC_L', 'UNC_R', 'GCC', 'SCC'
    ]
    
    # Create diagnosis data
    diagnosis_records = []
    for i in range(n_subjects):
        group = 'CN' if i < n_subjects // 2 else 'AD'
        diagnosis_records.append({
            'LONIUID': f'I{100000 + i}',
            'Group': group,
            'EXAMDATE': f'2024-0{(i % 9) + 1}-15'
        })
    
    diagnosis_df = pd.DataFrame(diagnosis_records)
    
    # Create DTI data with FA values
    dti_records = []
    for i in range(n_subjects):
        group = 'CN' if i < n_subjects // 2 else 'AD'
        
        # CN: higher FA, AD: lower FA
        if group == 'CN':
            fa_values = np.random.normal(0.50, 0.04, len(tract_names))
        else:
            fa_values = np.random.normal(0.42, 0.05, len(tract_names))
        
        fa_values = np.clip(fa_values, 0.1, 0.9)
        
        dti_record = {'LONIUID': f'I{100000 + i}'}
        for tract, fa in zip(tract_names, fa_values):
            dti_record[tract] = fa
        
        dti_records.append(dti_record)
    
    dti_df = pd.DataFrame(dti_records)
    
    # Save to examples/ directory
    output_dir = Path(__file__).parent
    diagnosis_df.to_csv(output_dir / 'diagnosis.csv', index=False)
    dti_df.to_csv(output_dir / 'DTI.csv', index=False)
    
    print(f"Simulated ADNI data for {n_subjects} subjects")
    print(f"Saved in: {output_dir}")
    return str(output_dir)


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


def prepare_visualization_data(summary_df, coords_df):
    """
    Merge summary statistics with coordinates for visualization.
    
    Parameters
    ----------
    summary_df : pd.DataFrame
        Group-level means (from compute_summary_statistics)
    coords_df : pd.DataFrame
        Tract coordinates
        
    Returns
    -------
    pd.DataFrame
        Visualization-ready data
    """
    # Transform from wide to long format
    metadata_cols = ['Group', 'LONIUID', 'EXAMDATE', 'STATUS', 'id']
    tract_cols = [c for c in summary_df.columns if c not in metadata_cols]
    
    viz_records = []
    for row in summary_df.itertuples(index=False):
        for tract in tract_cols:
            viz_records.append({
                'tract_id': tract,
                'diagnosis': row.Group,
                'metric_value': getattr(row, tract)
            })
    
    viz_df = pd.DataFrame(viz_records)
    
    # Merge with coordinates
    merged = pd.merge(
        viz_df,
        coords_df,
        left_on='tract_id',
        right_on='roi',
        how='inner'
    )
    
    # Select final columns
    final_cols = [
        'tract_id', 'start_x', 'start_y', 'start_z',
        'end_x', 'end_y', 'end_z', 'diagnosis', 'metric_value'
    ]
    
    viz_data = merged[final_cols]
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
    
    print("Data validation passed")
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
    Main workflow demonstrating complete pipeline with neuroconnect.data_prep.
    """
    
    # Step 1: Simulate ADNI data (or use your real data folder)
    data_folder = simulate_adni_data(n_subjects=40)
    
    # Step 2: Load data using load_data()
    diagnosis_df, dti_df = load_data(data_folder)
    
    # Step 3: Clean and merge with clean_data()
    merged_df, excluded = clean_data(diagnosis_df, dti_df)
    print(f"Merged data: {len(merged_df)} subjects")
    print(f"Excluded: {excluded} subjects")
    print()
    
    # Step 4: Calculate group means with compute_summary_statistics()
    summary_df = compute_summary_statistics(merged_df)
    
    # Step 5: Load coordinates
    coords = load_jhu_coordinates()
    
    # Step 6: Merge with coordinates
    viz_data = prepare_visualization_data(summary_df, coords)
    
    # Step 7: Validate format
    validate_data_format(viz_data)
    
    # Step 8: Save for upload
    save_for_upload(viz_data)
    
    # Summary
    print(f"Processed {len(merged_df)} subjects")
    print(f"Generated data for {len(viz_data['tract_id'].unique())} tracts")
    print(f"Groups: {sorted(viz_data['diagnosis'].unique())}")
    print()
    print("Next steps:")
    print("1. Review 'custom_neuroconnect_data.csv'")
    print("2. Upload to https://cpineda.shinyapps.io/neuroconnect/")
    print("3. Click 'Render / Update' to visualize")
    print()
    print("* To use YOUR data: Replace simulate_adni_data() with your")
    print("  actual ADNI folder path and run load_data() on it")


if __name__ == '__main__':
    main()
