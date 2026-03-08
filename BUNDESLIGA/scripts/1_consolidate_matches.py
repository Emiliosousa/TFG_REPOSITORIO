import pandas as pd
import os
import glob

# === CONFIGUTATION ===
SOURCE_DIR = os.path.join(os.path.dirname(__file__), '../data')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '../data/processed/matches_raw.csv')

# Official Name Mapping for Bundesliga
TEAM_MAPPING = {
    'Bayern Munich': 'Bayern Munich',
    'Dortmund': 'Borussia Dortmund',
    'Leverkusen': 'Bayer Leverkusen',
    'RB Leipzig': 'RB Leipzig',
    'M\'gladbach': 'Borussia Monchengladbach',
    'M''gladbach': 'Borussia Monchengladbach',
    'Wolfsburg': 'VfL Wolfsburg',
    'Frankfurt': 'Eintracht Frankfurt',
    'Hoffenheim': 'TSG Hoffenheim',
    'Freiburg': 'SC Freiburg',
    'Werder Bremen': 'Werder Bremen',
    'Mainz': 'FSV Mainz 05',
    'Mainz 05': 'FSV Mainz 05',
    'Union Berlin': 'Union Berlin',
    'FC Koln': 'FC Cologne',
    'Schalke 04': 'FC Schalke 04',
    'Stuttgart': 'VfB Stuttgart',
    'Augsburg': 'FC Augsburg',
    'Bochum': 'VfL Bochum',
    'Hertha': 'Hertha BSC',
    'Bielefeld': 'Arminia Bielefeld',
    'Darmstadt': 'SV Darmstadt 98',
    'Dusseldorf': 'Fortuna Dusseldorf',
    'Hannover': 'Hannover 96',
    'Nurnberg': 'FC Nurnberg',
    'Paderborn': 'SC Paderborn 07',
    'Greuther Furth': 'Greuther Furth',
    'Hamburger SV': 'Hamburger SV',
    'St Pauli': 'FC St. Pauli',
    'Heidenheim': '1. FC Heidenheim',
    'Holstein Kiel': 'Holstein Kiel'
}

def normalize_name(name):
    if not isinstance(name, str): return name
    name = name.strip()
    return TEAM_MAPPING.get(name, name)

def main():
    print("🚀 Starting Bundesliga Data Consolidation (2010-2026)...")
    
    # 1. Find all D1 csv files
    files = glob.glob(os.path.join(SOURCE_DIR, "D1*.csv"))
    print(f"📂 Found {len(files)} season files.")
    
    all_matches = []
    
    for f in files:
        try:
            df = pd.read_csv(f, encoding='latin1')
            
            # Filter essential columns
            cols = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HS', 'AS', 'HST', 'AST', 'HF', 'AF', 'HC', 'AC']
            # Check if columns exist
            if not all(c in df.columns for c in cols):
                print(f"⚠️ Skipping {os.path.basename(f)}: Missing columns.")
                continue
                
            # Add betting odds to base consolidation so we can calculate EV later
            b365_cols = ['B365H', 'B365D', 'B365A', 'MaxH', 'MaxD', 'MaxA']
            for bc in b365_cols:
                if bc in df.columns:
                    cols.append(bc)
                else: # Allow fallback missing odds
                    df[bc] = None
                    cols.append(bc)

            
            cols = list(dict.fromkeys(cols))
            
            df = df[cols].dropna(subset=['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']).copy()
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Date'])
            
            all_matches.append(df)
            print(f"   -> Loaded {os.path.basename(f)} ({len(df)} matches)")
            
        except Exception as e:
            print(f"❌ Error reading {f}: {e}")

    # 2. Merge
    if not all_matches:
        print("❌ No data loaded.")
        return

    df_final = pd.concat(all_matches, ignore_index=True)
    df_final = df_final.sort_values('Date')
    
    # 4. Standardize Teams
    df_final['HomeTeam'] = df_final['HomeTeam'].apply(normalize_name)
    df_final['AwayTeam'] = df_final['AwayTeam'].apply(normalize_name)
    
    # 5. Save
    print(f"💾 Saving {len(df_final)} matches to {OUTPUT_FILE}...")
    df_final.to_csv(OUTPUT_FILE, index=False)
    
    # Validation
    print("\n✅ VALIDATION REPORT:")
    print(f"- Total Rows: {len(df_final)}")
    print(f"- Columns: {list(df_final.columns)}")
    print(f"- Date Range: {df_final['Date'].min().date()} to {df_final['Date'].max().date()}")
    print(f"- Unique Teams ({df_final['HomeTeam'].nunique()}): {sorted(df_final['HomeTeam'].unique())[:5]}...")

if __name__ == "__main__":
    main()
