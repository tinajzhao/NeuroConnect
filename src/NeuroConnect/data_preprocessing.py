# could run into errors if multiple csvs in data outside of dti and diagnosis
import glob
import pandas as pd


# DATA LOADING
# INPUTS:
# OUTPUTS: 
def load_data():
    dti_df = None
    diagnosis_df = None
    
    for path in glob.glob("data/*.csv"):
        if "DTI" in path:
            dti_df = pd.read_csv(path)
        else:
            diagnosis_df = pd.read_csv(path)
    
    if dti_df is None or diagnosis_df is None:
        raise ValueError("Could not find both DTI and diagnosis files")
    
    return dti_df, diagnosis_df

# DATA MERGING AND CLEANING 
# INPUTS:
# OUTPUTS: 
# not sure on specific metric filter (ended up with 75 rows)
# if user specifies e.g. (FA) it could accidentally include columns such as MANUFACTURER
def clean_data(dti_df, diagnosis_df, metric_filter): 
    merged_df = dti_df.merge(diagnosis_df, how="left", left_on="PTID", right_on="subject_id")
    orig_len = len(merged_df)
    
    merged_df = merged_df[merged_df["entry_research_group"].isin(["AD", "CN"])]
    
    merged_df = merged_df.rename(columns={"entry_research_group": "diagnosis"})
    cols = list(merged_df.filter(like=metric_filter).columns) + ["PTID", "diagnosis"]
    merged_df = merged_df[cols]
    
    merged_df = merged_df.dropna()
    clean_len = len(merged_df)
    
    excluded = orig_len - clean_len
    
    return merged_df, excluded

# SUMMARY STATISTICS CALCULATION
# INPUTS:
# OUTPUTS: 
def calc_summary_stats(df):
    return 1

# SUMMARY STATISTICS EXPORT
# INPUTS:
# OUTPUTS: 
def export_summary_stats(df):
    return 1

# CALC GROUP DIFFERENCES
# INPUTS:
# OUTPUTS: 
def calc_group_diff(merged_df, difference_type="raw"):
    valid_diff_types = {"raw", "percent"}
    if difference_type not in valid_diff_types:
        raise ValueError(
            f"difference_type must be one of {valid_diff_types}, "
            f"but got '{difference_type}'.")
    
    grouped_df = merged_df.drop(columns=["PTID"]).groupby("diagnosis").mean()
    fa_diff = grouped_df.loc["AD"] - grouped_df.loc["CN"]

    if difference_type == "percent":
        fa_diff = fa_diff / grouped_df.loc["AD"] * 100
    
    return fa_diff 