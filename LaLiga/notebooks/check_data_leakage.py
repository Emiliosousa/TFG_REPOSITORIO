import pandas as pd
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt

def check_file(filepath):
    print(f"\n======== Checking {filepath} ========")
    if not os.path.exists(filepath):
        print("❌ File not found.")
        return

    df = pd.read_csv(filepath)
    print(f"Rows: {len(df)}")
    
    # Check if FTR exists
    if 'FTR' not in df.columns:
        print("⚠️ FTR column missing, cannot check target correlation.")
        return

    # Map target
    df['Target_Num'] = df['FTR'].map({'H': 1, 'D': 0, 'A': -1})
    if df['Target_Num'].isnull().all():
         df['Target_Num'] = df['FTR'].map({'H': 2, 'D': 1, 'A': 0}) # Try other mapping

    # Features to check
    features = [c for c in df.columns if 'L5' in c or 'Elo' in c]
    
    print(f"Analyzing {len(features)} features for leakage...")
    
    leak_suspects = []
    
    for f in features:
        if df[f].dtype not in [np.float64, np.int64]:
            continue
            
        # Correlación con el resultado (Target)
        corr = df[f].corr(df['Target_Num'])
        
        # Correlación con Goles (si existen)
        corr_goals = 0
        if 'FTHG' in df.columns and 'Home' in f:
            corr_goals = df[f].corr(df['FTHG'])
        elif 'FTAG' in df.columns and 'Away' in f:
            corr_goals = df[f].corr(df['FTAG'])
            
        # Si la correlación es muy alta, es sospechoso
        # Un promedio de 5 partidos NO debería correlacionar > 0.5 con el resultado de HOY
        if abs(corr) > 0.4 or abs(corr_goals) > 0.6:
            leak_suspects.append((f, corr, corr_goals))
            print(f"🚨 LEAK SUSPECT: {f} | Corr w/Result: {corr:.3f} | Corr w/Goals: {corr_goals:.3f}")
            
    if not leak_suspects:
        print("✅ No obvious leakage correlations found in rolling features.")
    else:
        print(f"❌ Found {len(leak_suspects)} suspicious features.")

    # Check if Home_xG_Avg_L5 is identical to current xG proxy (common bug)
    if 'Home_xG_Proxy' in df.columns and 'Home_xG_Avg_L5' in df.columns:
        exact_matches = (df['Home_xG_Proxy'] == df['Home_xG_Avg_L5']).sum()
        print(f"Exact matches between Current xG and Avg L5: {exact_matches} / {len(df)}")
        if exact_matches > len(df) * 0.1:
            print("🚨 MAJOR LEAK: Rolling average equals current value in many rows!")

# Check both files
check_file('df_final_clean.csv')
check_file('../df_final_app.csv')
check_file('df_final_app.csv')
