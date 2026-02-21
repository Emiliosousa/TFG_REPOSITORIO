import pandas as pd
import numpy as np
import os

def audit_correlations():
    path = '../../Premier/df_premier_features.csv'
    if not os.path.exists(path):
        print("File not found")
        return

    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    
    if 'FTR' not in df.columns:
        print("No FTR column")
        return

    # Map target
    df['Target_Num'] = df['FTR'].map({'H': 1, 'D': 0, 'A': -1})
    
    # Check all numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    print("\n--- Correlations with Result (Home Win=1, Away=-1) ---")
    corrs = []
    for col in numeric_df.columns:
        if col == 'Target_Num': continue
        c = df[col].corr(df['Target_Num'])
        corrs.append((col, c))
    
    # Sort by absolute correlation
    corrs.sort(key=lambda x: abs(x[1]), reverse=True)
    
    for name, val in corrs[:20]:
        print(f"{name}: {val:.4f}")
        if abs(val) > 0.7:
            print(f"  🚨 SUSPICIOUSLY HIGH correlation!")

if __name__ == "__main__":
    audit_correlations()
