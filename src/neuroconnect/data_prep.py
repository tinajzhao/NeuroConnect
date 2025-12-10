import pandas as pd
import os

def load_data(data_folder):
    """
    Loads diagnosis.csv and DTI.csv from the specified folder.
    
    Raises:
        FileNotFoundError: If either file is missing.
    """
    diag_path = os.path.join(data_folder, 'diagnosis.csv')
    dti_path = os.path.join(data_folder, 'DTI.csv')
    
    if not os.path.exists(diag_path):
        raise FileNotFoundError(f"File not found: {diag_path}")
    if not os.path.exists(dti_path):
        raise FileNotFoundError(f"File not found: {dti_path}")
        
    diagnosis_df = pd.read_csv(diag_path, dtype={'LONIUID': str})
    dti_df = pd.read_csv(dti_path, dtype={'LONIUID': str})
    return diagnosis_df, dti_df

def clean_data(diagnosis_df, dti_df):
    """
    Merges diagnosis and DTI data on 'LONIUID'.
    Filters for relevant groups (AD, CN) and handles missing values.
    """
    # Ensure consistent string type for merge key
    diagnosis_df['LONIUID'] = diagnosis_df['LONIUID'].astype(str)
    dti_df['LONIUID'] = dti_df['LONIUID'].astype(str)
    
    # Merge data
    merged_df = pd.merge(diagnosis_df, dti_df, on='LONIUID', how='inner')
    orig_len = len(merged_df)
    
    # Filter for AD and CN groups only
    if 'Group' in merged_df.columns:
        merged_df = merged_df[merged_df['Group'].isin(['AD', 'CN'])]
    
    # Drop rows with missing values in critical columns
    # Assuming all columns are critical for now
    merged_df = merged_df.dropna()
    clean_len = len(merged_df)
    
    excluded = orig_len - clean_len
    
    return merged_df, excluded

def compute_summary_statistics(cleaned_df):
    """
    Calculates mean for each tract for each group of AD and CN
    """
    if cleaned_df.empty:
        return pd.DataFrame()

    # Identify tract columns (numeric columns excluding metadata)
    metadata_cols = ['LONIUID', 'Group', 'EXAMDATE', 'STATUS', 'id']
    tract_cols = [c for c in cleaned_df.columns if c not in metadata_cols and pd.api.types.is_numeric_dtype(cleaned_df[c])]
    
    if not tract_cols:
        return pd.DataFrame()

    # Calculate mean by Group
    summary = cleaned_df.groupby('Group')[tract_cols].mean().reset_index()
    return summary

def format_output(summary_df):
    """
    Formats the summary data for visualization input
    """
    if summary_df.empty:
        return []
    return summary_df.to_dict(orient='records')

def calc_group_diff(merged_df, difference_type="raw"):
    """
    Groups by diagnosis and calculates difference for each tract
    """
    valid_diff_types = {"raw", "percent"}
    if difference_type not in valid_diff_types:
        raise ValueError(
            f"difference_type must be one of {valid_diff_types}, "
            f"but got '{difference_type}'.")
    
    grouped_df = merged_df.drop(columns=["PTID"]).groupby("diagnosis").mean()
    
    required_groups = ["AD", "CN"]

    missing = [g for g in required_groups if g not in grouped_df.index]
    if missing:
        raise KeyError(f"Missing expected diagnosis group(s): {missing}")
    
    fa_diff = grouped_df.loc["AD"] - grouped_df.loc["CN"]

    if difference_type == "percent":
        fa_diff = fa_diff / grouped_df.loc["AD"] * 100
    
    return fa_diff 