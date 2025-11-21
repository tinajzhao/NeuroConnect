import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_synthetic_data(num_rows=50):
    # EXAMDATE: Random dates
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=random.randint(0, 365)) for _ in range(num_rows)]
    exam_dates = [d.strftime('%Y-%m-%d') for d in dates]
    
    # LONIUID: Strictly 6-character numeric strings
    loni_uids = [str(random.randint(100000, 999999)) for _ in range(num_rows)]
    
    # STATUS: Set to 'Complete'
    statuses = ["Complete"] * num_rows
    
    # AD_CST_L: Normal distribution (mean 0.001307, std 0.00018663)
    ad_cst_l = np.random.normal(0.001307, 0.00018663, num_rows)
    
    # AD_CST_R: Normal distribution (mean 0.0012545, std 0.000167566)
    ad_cst_r = np.random.normal(0.0012545, 0.000167566, num_rows)

    df = pd.DataFrame({
        'EXAMDATE': exam_dates,
        'LONIUID': loni_uids,
        'STATUS': statuses,
        'AD_CST_L': ad_cst_l,
        'AD_CST_R': ad_cst_r
    })
    
    output_path = os.path.join(os.path.dirname(__file__), 'synthetic_data.csv')
    df.to_csv(output_path, index=False)
    print(f"Generated synthetic data at {output_path}")

if __name__ == "__main__":
    generate_synthetic_data()