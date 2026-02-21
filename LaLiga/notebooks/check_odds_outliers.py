import pandas as pd
import os

def check_odds(filepath):
    print(f"\nChecking odds in {filepath}...")
    if not os.path.exists(filepath):
        print("File not found.")
        return

    df = pd.read_csv(filepath)
    
    # 1. Check for Odds > 10 that WON
    print("\n--- High Odds Winners ---")
    high_odds_threshold = 10.0
    
    for side in ['H', 'D', 'A']:
        col = f'B365{side}'
        if col not in df.columns: continue
        
        # Filter: Odds > 10 AND Won
        mask = (df[col] > high_odds_threshold) & (df['FTR'] == side)
        winners = df[mask]
        
        if not winners.empty:
            print(f"[{side}] Found {len(winners)} winners with Odds > {high_odds_threshold}:")
            for _, row in winners.iterrows():
                print(f"  {row['Date']} {row['HomeTeam']} vs {row['AwayTeam']} | {side} @ {row[col]}")
        else:
            print(f"[{side}] No winners > {high_odds_threshold}")

    # 2. Check for Impossible Odds (e.g. < 1.01)
    print("\n--- Invalid Odds (< 1.01) ---")
    for col in ['B365H', 'B365D', 'B365A']:
        bad = df[df[col] < 1.01]
        if not bad.empty:
            print(f"{col}: {len(bad)} invalid values")
            print(bad[[col, 'HomeTeam', 'AwayTeam']].head())

    # 3. Check for Suspicious Favorites (Odds > 5.0 but implied prob > 50%?)
    # Hard to check without model.
    
    # 4. Check for Massive Odds (Typos like 100.0)
    print("\n--- Massive Odds (> 50.0) ---")
    for col in ['B365H', 'B365D', 'B365A']:
        massive = df[df[col] > 50.0]
        if not massive.empty:
            print(f"{col}: {len(massive)} matches > 50.0")
            print(massive[[col, 'HomeTeam', 'AwayTeam', 'FTR']])

if __name__ == "__main__":
    check_odds('df_final_clean.csv')
    check_odds('../df_final_app.csv')
