import pandas as pd
import json
import os
import difflib

# Paths
CSV_PATH = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\df_final_app.csv"
SOFIFA_PATH = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\data\sofifa_history.json"
TM_PATH = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\data\transfermarkt_history.json"

def check_data():
    print("--- DATA INTEGRITY CHECK ---")
    
    # 1. Check Files
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV Not Found: {CSV_PATH}")
        return
    if not os.path.exists(SOFIFA_PATH):
        print(f"❌ Sofifa JSON Not Found: {SOFIFA_PATH}")
        return
    if not os.path.exists(TM_PATH):
        print(f"❌ Transfermarkt JSON Not Found: {TM_PATH}")
        return
        
    print("✅ All data files present.")
    
    # 2. Load Data
    df = pd.read_csv(CSV_PATH)
    print(f"CSV Rows: {len(df)}")
    print(f"Seasons: {df['Season'].unique()}")
    
    with open(SOFIFA_PATH, 'r', encoding='utf-8') as f:
        sofifa = json.load(f)
    with open(TM_PATH, 'r', encoding='utf-8') as f:
        tm = json.load(f)
        
    # 3. Check Team Matching for a sample season
    sample_season = str(int(df['Season'].max()))
    print(f"\nChecking Matching for Season {sample_season}...")
    
    if sample_season not in sofifa:
        print(f"⚠️ Season {sample_season} NOT in Sofifa keys: {list(sofifa.keys())}")
    else:
        fifa_teams = [t['team'] for t in sofifa[sample_season]]
        csv_teams = df[df['Season'] == int(sample_season)]['HomeTeam'].unique()
        
        print(f"CSV Teams in {sample_season}: {len(csv_teams)}")
        print(f"FIFA Teams in {sample_season}: {len(fifa_teams)}")
        
        matches = 0
        mismatches = []
        for team in csv_teams:
            match = difflib.get_close_matches(team, fifa_teams, n=1, cutoff=0.6)
            if match:
                matches += 1
            else:
                mismatches.append(team)
                
        print(f"✅ Successful FIFA Matches: {matches}")
        if mismatches:
            print(f"❌ Missed Matches ({len(mismatches)}): {mismatches}")
            print("   (These will result in 'fictitious' imputed data)")
            
    # 4. Check Transfermarkt Matching
    if sample_season not in tm:
        print(f"⚠️ Season {sample_season} NOT in TM keys: {list(tm.keys())}")
    else:
        tm_teams = [t['team'] for t in tm[sample_season]]
        csv_teams = df[df['Season'] == int(sample_season)]['HomeTeam'].unique()
        
        matches = 0
        mismatches = []
        for team in csv_teams:
            match = difflib.get_close_matches(team, tm_teams, n=1, cutoff=0.6)
            if match:
                matches += 1
            else:
                mismatches.append(team)
        
        print(f"✅ Successful TM Matches: {matches}")
        if mismatches:
            print(f"❌ Missed Matches ({len(mismatches)}): {mismatches}")

if __name__ == "__main__":
    check_data()
