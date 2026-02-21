import pandas as pd
import numpy as np
import sys
import os

# Adjust path to find src (parent directory of notebooks)
sys.path.append(os.path.dirname(os.getcwd()))
try:
    from src.feature_engineering import generate_features
except ImportError:
    # Try adding one more level up if running from root
    sys.path.append(os.path.join(os.getcwd(), 'LaLiga'))
    from src.feature_engineering import generate_features

def test_leakage():
    print("TESTING FEATURE ENGINEERING FOR LEAKAGE...")
    
    # Create dummy match history for Team A
    # Match 1: 2024-01-01. Team A (Home). HS=10. FTR=H. (Home_xG ~ 0.9 + HST...)
    # Match 2: 2024-01-08. Team A (Home). HS=20. FTR=H.
    # Match 3: 2024-01-15. Team A (Home). HS=0.  FTR=A.
    
    data = {
        'Date': ['01/01/2024', '08/01/2024', '15/01/2024'],
        'HomeTeam': ['TeamA', 'TeamA', 'TeamA'],
        'AwayTeam': ['TeamB', 'TeamC', 'TeamD'],
        'FTHG': [2, 3, 0],
        'FTAG': [0, 0, 1],
        'FTR': ['H', 'H', 'A'],
        'HS': [10, 20, 0], # Shots: 10, 20, 0
        'AS': [2, 2, 10],
        'HST': [5, 10, 0],
        'AST': [1, 1, 5],
        'HF': [10, 10, 10], 'AF': [10, 10, 10],
        'HY': [0,0,0], 'AY': [0,0,0], 'HR': [0,0,0], 'AR': [0,0,0],
        'HC': [5, 5, 0], 'AC': [1, 1, 5], 
        'Season': [2024, 2024, 2024]
    }
    
    df = pd.DataFrame(data)
    
    # Run pipeline
    df_out = generate_features(df)
    
    # Check Match 2
    # It should assume stats from Match 1.
    # Match 1 Home_xG (approx) = 10*0.09 + 5*0.29 = 0.9 + 1.45 = 2.35
    # Match 2 Home_xG (approx) = 20*0.09 + 10*0.29 = 1.8 + 2.9 = 4.7
    
    # Match 2 'Home_xG_Avg_L5' should be approx 2.35 (Average of Match 1).
    # If leakage, it might include Match 2 stats (4.7) or avg of both.
    
    m2 = df_out.iloc[1]
    print(f"Match 2 (Row 1) - Date: {m2['Date']}")
    print(f"Match 2 Raw HS: {m2['HS']}")
    print(f"Match 2 PostMatch_xG: {m2.get('PostMatch_Home_xG', 'Dropped')}")
    print(f"Match 2 Home_xG_Avg_L5: {m2['Home_xG_Avg_L5']}")
    
    # Verify
    # Match 1 xG = 2.35
    expected_m2_roll = 2.35
    
    if abs(m2['Home_xG_Avg_L5'] - expected_m2_roll) < 0.1:
        print("✅ Rolling Window Shift looks CORRECT. (Match 2 sees Match 1 stats)")
    else:
        print(f"❌ Rolling Window Shift FAILED. Expected ~{expected_m2_roll}, Got {m2['Home_xG_Avg_L5']}")
        # Check if it matches current
        current_xg = (20*0.09 + 10*0.29)
        if abs(m2['Home_xG_Avg_L5'] - current_xg) < 0.1:
             print("🚨 LEAKAGE DETECTED: Feature matches CURRENT match stats.")
        elif abs(m2['Home_xG_Avg_L5'] - (current_xg + expected_m2_roll)/2) < 0.1:
             print("🚨 LEAKAGE DETECTED: Feature includes CURRENT match in average.")

    # Check Match 1
    # Should be 0 or small epsilon/default
    m1 = df_out.iloc[0]
    print(f"Match 1 Home_xG_Avg_L5: {m1['Home_xG_Avg_L5']}")
    if m1['Home_xG_Avg_L5'] == 0:
        print("✅ Match 1 has no history (0). Correct.")
    else:
        print(f"⚠️ Match 1 has non-zero history: {m1['Home_xG_Avg_L5']}")

if __name__ == "__main__":
    test_leakage()
