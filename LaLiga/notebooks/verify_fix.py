import pandas as pd
import numpy as np

def verify():
    print("VERIFYING LEAKAGE FIX...")
    try:
        df = pd.read_csv('../df_final_app.csv')
    except:
        df = pd.read_csv('df_final_app.csv')

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    # Calculate Raw xG
    df['Home_xG'] = (df['HS'] * 0.09) + (df['HST'] * 0.29)
    df['Away_xG'] = (df['AS'] * 0.09) + (df['AST'] * 0.29)
    
    # Reconstruct Full Schedule for Team
    team = "Real Madrid"
    
    # Get Home Games
    h = df[df['HomeTeam'] == team][['Date', 'HomeTeam', 'Home_xG', 'Home_xG_Avg_L5']].copy()
    h.columns = ['Date', 'Team', 'xG', 'Dataset_Roll']
    
    # Get Away Games
    a = df[df['AwayTeam'] == team][['Date', 'AwayTeam', 'Away_xG', 'Away_xG_Avg_L5']].copy()
    a.columns = ['Date', 'Team', 'xG', 'Dataset_Roll']
    
    # Combine and Sort
    full_schedule = pd.concat([h, a]).sort_values('Date')
    
    # Calculate Rolling
    full_schedule['Manual_Roll'] = full_schedule['xG'].shift(1).rolling(5, min_periods=1).mean()
    full_schedule['Diff'] = full_schedule['Dataset_Roll'] - full_schedule['Manual_Roll']
    
    recent = full_schedule[full_schedule['Date'] > '2024-01-01']
    
    print(f"\nChecking {team} Full Schedule ({len(full_schedule)} matches)")
    
    cols = ['Date', 'xG', 'Dataset_Roll', 'Manual_Roll', 'Diff']
    
    # Check Max Diff
    max_diff = recent['Diff'].abs().max()
    print(f"\nMax Difference (Manual Shifted vs Dataset): {max_diff}")
    
    if max_diff < 0.001:
        print("✅ SUCCESS: Dataset Features match Manual Shifted Calculation.")
    else:
        print("❌ FAILURE: Mismatch detected.")
        print("Top 5 Mismatches:")
        print(recent.nlargest(5, 'Diff')[cols])
        
        # Check if it matches UN-shifted
        full_schedule['Manual_Roll_NoShift'] = full_schedule['xG'].rolling(5, min_periods=1).mean()
        diff_noshift = (full_schedule['Dataset_Roll'] - full_schedule['Manual_Roll_NoShift']).abs().max()
        print(f"   Diff with NO SHIFT: {diff_noshift}")

if __name__ == "__main__":
    verify()
