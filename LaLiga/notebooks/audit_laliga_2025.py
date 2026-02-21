import pandas as pd
import numpy as np
import os

def audit_2025():
    print("AUDITING LA LIGA 2025 DATA FOR LEAKAGE")
    
    # Try different paths
    paths = [
        'df_final_app.csv',
        '../df_final_app.csv',
        '../../df_final_app.csv',
        'df_final_clean.csv'
    ]
    
    df = None
    for p in paths:
        if os.path.exists(p):
            print(f"Loaded: {p}")
            df = pd.read_csv(p)
            break
            
    if df is None:
        print("❌ Could not find df_final_app.csv")
        return

    # Convert date
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        # Filter 2025
        mask_2025 = df['Date'].dt.year == 2025
        df_2025 = df.loc[mask_2025]
        print(f"2025 Records: {len(df_2025)}")
    else:
        print("Date column missing, checking all data")
        df_2025 = df

    # 1. Direct Leakage Check (Rolling == Current)
    # Check if 'Home_xG' exists (the raw stat)
    xg_cols = [c for c in df.columns if 'xG' in c and 'Avg' not in c]
    print(f"Raw xG Columns found: {xg_cols}")
    
    leaks = 0
    if 'Home_xG' in df.columns and 'Home_xG_Avg_L5' in df.columns:
        for idx, row in df_2025.iterrows():
            if row['Home_xG'] == row['Home_xG_Avg_L5'] and row['Home_xG'] > 0:
                leaks += 1
        print(f"🚨 Direct Leakage (Current xG == Avg L5): {leaks} rows")
    else:
        print("⚠️ Cannot check direct match (missing raw xG column)")

    # 2. Correlation Check (Result vs Features) in 2025
    if 'FTR' in df_2025.columns:
        df_2025['Target_Num'] = df_2025['FTR'].map({'H': 2, 'D': 1, 'A': 0})
        numeric_cols = df_2025.select_dtypes(include=[np.number]).columns
        
        print("\n--- Correlations in 2025 Subset ---")
        suspicious = []
        for col in numeric_cols:
            if col == 'Target_Num': continue
            corr = df_2025[col].corr(df_2025['Target_Num'])
            if abs(corr) > 0.5:
                suspicious.append((col, corr))
                print(f"{col}: {corr:.4f}")
        
        if not suspicious:
            print("✅ No highly correlated features found.")
        else:
            print(f"⚠️ Found {len(suspicious)} highly correlated features.")

if __name__ == "__main__":
    audit_2025()
