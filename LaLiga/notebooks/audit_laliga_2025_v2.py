import pandas as pd
import numpy as np
import os
import sys

def audit_2025():
    with open("audit_results.txt", "w", encoding="utf-8") as f:
        f.write("AUDITING LA LIGA 2025 DATA FOR LEAKAGE\n")
        
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
                f.write(f"Loaded: {p}\n")
                df = pd.read_csv(p)
                break
                
        if df is None:
            f.write("❌ Could not find df_final_app.csv\n")
            return

        # Convert date
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            # Filter 2025
            mask_2025 = df['Date'].dt.year == 2025
            df_2025 = df.loc[mask_2025]
            f.write(f"2025 Records: {len(df_2025)}\n")
        else:
            f.write("Date column missing, scanning all rows.\n")
            df_2025 = df

        # 1. Direct Leakage Check (Rolling == Current)
        f.write("\n-- Direct Leakage Check --\n")
        xg_cols = [c for c in df.columns if 'xG' in c and 'Avg' not in c]
        f.write(f"Raw xG Cols: {xg_cols}\n")
        
        leaks = 0
        if 'Home_xG' in df.columns and 'Home_xG_Avg_L5' in df.columns:
            for idx, row in df_2025.iterrows():
                # Check if Avg L5 exactly matches current xG (implies window size 1 including current)
                if abs(row['Home_xG'] - row['Home_xG_Avg_L5']) < 0.0001 and row['Home_xG'] > 0:
                    leaks += 1
            f.write(f"🚨 Direct Leakage (Current xG == Avg L5): {leaks} rows\n")
        else:
             f.write("⚠️ Cannot check direct match (missing raw xG column)\n")

        # 2. Check for Future Info in Rolling Columns
        # If Rolling L5 includes current match, correlation with Target will be artificially high
        if 'FTR' in df_2025.columns:
            df_2025['Target_Num'] = df_2025['FTR'].map({'H': 2, 'D': 1, 'A': 0})
            numeric_cols = df_2025.select_dtypes(include=[np.number]).columns
            
            f.write("\n-- Correlations in 2025 Subset (> 0.4) --\n")
            suspicious = []
            for col in numeric_cols:
                if col == 'Target_Num': continue
                # Skip IDs or non-features
                if 'ID' in col or 'season' in col.lower(): continue
                
                corr = df_2025[col].corr(df_2025['Target_Num'])
                if abs(corr) > 0.4:
                    suspicious.append((col, corr))
                    f.write(f"{col}: {corr:.4f}\n")
            
            if not suspicious:
                f.write("✅ No highly correlated features found (> 0.4).\n")
            else:
                f.write(f"⚠️ Found {len(suspicious)} highly correlated features.\n")

        # 3. Check for specific columns anomalies
        if 'B365H' in df_2025.columns:
             min_odds = df_2025['B365H'].min()
             max_odds = df_2025['B365H'].max()
             f.write(f"\nOdds Range B365H: {min_odds} to {max_odds}\n")

if __name__ == "__main__":
    audit_2025()
