"""
Example 1: Basic Visualization with Demo Data
==============================================

This example demonstrates the simplest workflow for creating visualization-ready
data using pre-extracted JHU coordinates and synthetic DTI metrics.

Use this example to:
- Understand the required data format
- Learn how to use neuroconnect functions
- Test the visualization pipeline
- Create quick demos with sample data

No atlas extraction needed - uses pre-generated jhu_coordinates.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from neuroconnect.data_prep import compute_summary_statistics


def load_jhu_coordinates():
    """
    Load pre-extracted JHU tract coordinates.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: roi, start_x/y/z, end_x/y/z, centroid_x/y/z
    """
    # Path to pre-extracted coordinates (included in repository)
    coord_file = Path(__file__).parent.parent / 'data' / 'jhu_coordinates.csv'

    if not coord_file.exists():
        raise FileNotFoundError(
            f"Coordinates file not found at {coord_file}\n"
            "Make sure you're running from the project directory."
        )

    coords_df = pd.read_csv(coord_file)
    print(f"Loaded {len(coords_df)} tract coordinates")
    return coords_df


def generate_demo_subject_data(n_subjects_per_group=20):
    """
    Generate synthetic subject-level DTI data.
    
    Creates realistic FA values for each tract with individual variation.
    This format matches what data_prep expects (LONIUID, Group, tract columns).
    
    Parameters
    ----------
    n_subjects_per_group : int
        Number of subjects per diagnostic group (CN and AD)
        
    Returns
    -------
    pd.DataFrame
        Subject-level DTI data
    """
    np.random.seed(42)

    # JHU tract names (subset for demonstration)
    tract_names = [
        'ATR_L', 'ATR_R', 'CST_L', 'CST_R', 'CGC_L', 'CGC_R',
        'FX_MAJOR', 'IFO_L', 'IFO_R', 'ILF_L', 'ILF_R',
        'SLF_L', 'SLF_R', 'UNC_L', 'UNC_R', 'GCC', 'SCC'
    ]

    subjects = []
    total_subjects = n_subjects_per_group * 2

    for i in range(total_subjects):
        group = 'CN' if i < n_subjects_per_group else 'AD'

        # CN subjects have higher FA values (healthier white matter)
        if group == 'CN':
            fa_values = np.random.normal(0.50, 0.04, len(tract_names))
        else:
            fa_values = np.random.normal(0.42, 0.05, len(tract_names))

        fa_values = np.clip(fa_values, 0.1, 0.9)

        # Create subject record in ADNI format
        subject_data = {'LONIUID': f'S{i+1:04d}', 'Group': group}
        for tract, fa in zip(tract_names, fa_values):
            subject_data[tract] = fa

        subjects.append(subject_data)

    df = pd.DataFrame(subjects)
    print(f"Generated demo data for {total_subjects} subjects")
    return df


def prepare_for_visualization(subject_df, coords_df):
    """
    Transform subject-level data to visualization format.
    
    Uses compute_summary_statistics() to calculate group means,
    then merges with tract coordinates.
    
    Parameters
    ----------
    subject_df : pd.DataFrame
        Subject-level DTI data (LONIUID, Group, tract columns)
    coords_df : pd.DataFrame
        Tract coordinates (roi, start_x/y/z, end_x/y/z)
        
    Returns
    -------
    pd.DataFrame
        Visualization-ready data
    """
    summary_df = compute_summary_statistics(subject_df)

    if summary_df.empty:
        raise ValueError("Failed to compute summary statistics")

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

    result = merged[final_cols]
    print(f"Merged data: {len(result)} records")
    return result


def save_visualization_data(viz_data, output_file='demo_visualization_data.csv'):
    """
    Save visualization-ready data to CSV.
    
    Parameters
    ----------
    viz_data : pd.DataFrame
        Complete data with coordinates and metrics
    output_file : str
        Output filename
    """
    output_path = Path(__file__).parent / output_file
    viz_data.to_csv(output_path, index=False)
    print(f"Saved to: {output_path}")


def main():
    """
    Main demonstration workflow.
    """

    # Step 1: Load pre-extracted coordinates
    coords_df = load_jhu_coordinates()

    # Step 2: Generate subject-level DTI data
    subject_df = generate_demo_subject_data(n_subjects_per_group=20)

    # Step 3: Process with neuroconnect and prepare for visualization
    viz_data = prepare_for_visualization(subject_df, coords_df)

    # Step 4: Save for visualization
    save_visualization_data(viz_data)

    # Summary
    print(f"Processed {len(subject_df)} subjects")
    print(f"Generated {len(viz_data['tract_id'].unique())} tracts")
    print(f"Groups: {sorted(viz_data['diagnosis'].unique())}")
    print("\nMean FA by group:")
    print(viz_data.groupby('diagnosis')['metric_value'].mean())
    print()
    print("Next steps:")
    print("1. Open https://cpineda.shinyapps.io/neuroconnect/")
    print("2. Upload 'demo_visualization_data.csv'")
    print("3. Click 'Render / Update' to visualize")

if __name__ == '__main__':
    main()
