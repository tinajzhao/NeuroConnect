"""
Example 1: Basic Visualization with Demo Data
==============================================

This example demonstrates the simplest workflow for creating visualization-ready
data using pre-extracted JHU coordinates and synthetic DTI metrics.

Use this example to:
- Understand the required data format
- Test the visualization pipeline
- Create quick demos with sample data

No atlas extraction needed - uses pre-generated jhu_coordinates.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path


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
    print(f"✓ Loaded {len(coords_df)} tract coordinates")
    return coords_df


def generate_demo_dti_data(coords_df, diagnosis='CN', mean_fa=0.45, std_fa=0.05):
    """
    Generate synthetic DTI data for demonstration.
    
    Creates realistic FA values for each tract with some random variation.
    
    Parameters
    ----------
    coords_df : pd.DataFrame
        Tract coordinate data
    diagnosis : str
        Diagnostic group ('CN' or 'AD')
    mean_fa : float
        Mean fractional anisotropy value
    std_fa : float
        Standard deviation for FA values
        
    Returns
    -------
    pd.DataFrame
        Synthetic DTI data with FA values for each tract
    """
    np.random.seed(42)  # For reproducibility
    
    # Generate random FA values for each tract
    n_tracts = len(coords_df)
    fa_values = np.random.normal(mean_fa, std_fa, n_tracts)
    
    # Clip to realistic FA range [0, 1]
    fa_values = np.clip(fa_values, 0.1, 0.9)
    
    # Create demo data
    demo_data = pd.DataFrame({
        'tract_id': coords_df['roi'],
        'diagnosis': diagnosis,
        'metric_value': fa_values
    })
    
    print(f"Generated demo data for {diagnosis} group")
    return demo_data


def merge_coordinates_and_metrics(coords_df, dti_df):
    """
    Merge tract coordinates with DTI metrics.
    
    Creates the final format needed for visualization: coordinates + metrics.
    
    Parameters
    ----------
    coords_df : pd.DataFrame
        Tract coordinates (from jhu_coordinates.csv)
    dti_df : pd.DataFrame
        DTI metrics (FA values)
        
    Returns
    -------
    pd.DataFrame
        Merged data ready for visualization
    """
    merged = pd.merge(
        dti_df,
        coords_df,
        left_on='tract_id',
        right_on='roi',
        how='inner'
    )
    
    # Keep only necessary columns in correct order
    viz_data = merged[[
        'tract_id', 'start_x', 'start_y', 'start_z',
        'end_x', 'end_y', 'end_z', 'diagnosis', 'metric_value'
    ]]
    
    print(f"Merged data: {len(viz_data)} tracts")
    return viz_data


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
    
    Shows complete pipeline from coordinates to visualization-ready data.
    """

    # Step 1: Load pre-extracted coordinates
    coords_df = load_jhu_coordinates()
    print()
    
    # Step 2: Generate demo DTI data for both groups
    
    # Healthy controls - higher FA values
    cn_data = generate_demo_dti_data(
        coords_df, 
        diagnosis='CN', 
        mean_fa=0.50,  # Higher FA = healthier white matter
        std_fa=0.04
    )
    
    # Alzheimer's disease - lower FA values
    ad_data = generate_demo_dti_data(
        coords_df,
        diagnosis='AD',
        mean_fa=0.42,  # Lower FA = degraded white matter
        std_fa=0.05
    )
    
    # Combine both groups
    combined_dti = pd.concat([cn_data, ad_data], ignore_index=True)
    print()
    
    # Step 3: Merge coordinates with metrics
    viz_data = merge_coordinates_and_metrics(coords_df, combined_dti)
    print()
    
    # Step 4: Save for visualization
    save_visualization_data(viz_data)
    print()
    
    # Summary statistics
    print(f"Total tracts: {len(coords_df)}")
    print(f"CN subjects: {len(cn_data)} tracts")
    print(f"AD subjects: {len(ad_data)} tracts")
    print(f"\nMean FA by group:")
    print(viz_data.groupby('diagnosis')['metric_value'].mean())
    print()
    print("Next steps:")
    print("1. Open https://cpineda.shinyapps.io/neuroconnect/")
    print("2. Upload 'demo_visualization_data.csv'")
    print("3. Click 'Render / Update' to visualize")


if __name__ == '__main__':
    main()
