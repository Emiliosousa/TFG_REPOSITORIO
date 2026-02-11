import pandas as pd
import os
import glob
import unicodedata

# === CONFIGUTATION ===
SOURCE_DIR = os.path.join(os.path.dirname(__file__), '../data')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '../data/processed/matches_raw.csv')

# Official Name Mapping (Winamax/Premier Standard)
TEAM_MAPPING = {
    'Man United': 'Manchester United', 'Man City': 'Manchester City',
    'Spurs': 'Tottenham', 'Newcastle': 'Newcastle United',
    'Leicester': 'Leicester City', 'Norwich': 'Norwich City',
    'Leeds': 'Leeds United', 'Sheffield United': 'Sheffield Utd',
    'West Ham': 'West Ham United', 'Wolves': 'Wolverhampton Wanderers',
    'Brighton': 'Brighton & Hove Albion', 'Huddersfield': 'Huddersfield Town',
    'Cardiff': 'Cardiff City', 'Swansea': 'Swansea City',
    'Stoke': 'Stoke City', 'Hull': 'Hull City',
    'QPR': 'Queens Park Rangers', 'West Brom': 'West Bromwich Albion',
    'Bournemouth': 'AFC Bournemouth', 'Nott''m Forest': 'Nottingham Forest',
    'Luton': 'Luton Town', 'Ipswich': 'Ipswich Town'
}

def normalize_name(name):
    if not isinstance(name, str): return name
    name = name.strip()
    return TEAM_MAPPING.get(name, name)

def main():
    print("🚀 Starting Premier League Data Consolidation (2010-2026)...")
    
    # 1. Find all E0 csv files
    files = glob.glob(os.path.join(SOURCE_DIR, "E0-*.csv"))
    print(f"📂 Found {len(files)} season files.")
    
    all_matches = []
    
    for f in files:
        try:
            # Read CSV (handle encoding issues if any)
            df = pd.read_csv(f, encoding='latin1') # classic football-data encoding
            
            # Filter essential columns
            cols = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']
            # Check if columns exist
            if not all(c in df.columns for c in cols):
                print(f"⚠️ Skipping {os.path.basename(f)}: Missing columns.")
                continue
                
            df = df[cols].dropna()
            all_matches.append(df)
            print(f"   -> Loaded {os.path.basename(f)} ({len(df)} matches)")
            
        except Exception as e:
            print(f"❌ Error reading {f}: {e}")

    # 2. Merge
    if not all_matches:
        print("❌ No data loaded.")
        return

    df_final = pd.concat(all_matches, ignore_index=True)
    
    # 3. Process Dates
    # football-data.co.uk uses DD/MM/YY or DD/MM/YYYY. Pandas handles mixed with flexible parsing but dayfirst=True is safer
    df_final['Date'] = pd.to_datetime(df_final['Date'], dayfirst=True, errors='coerce')
    df_final = df_final.dropna(subset=['Date']).sort_values('Date')
    
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
