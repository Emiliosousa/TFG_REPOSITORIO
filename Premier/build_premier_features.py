"""
Premier League Feature Engineering Pipeline
Replicates the LaLiga 10-feature approach for Premier League data.
"""
import pandas as pd
import numpy as np
import os
import glob

# === CONFIG ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'df_premier_features.csv')

TEAM_MAPPING = {
    'Man United': 'Manchester United', 'Man City': 'Manchester City',
    'Spurs': 'Tottenham', 'Newcastle': 'Newcastle United',
    'Leicester': 'Leicester City', 'Norwich': 'Norwich City',
    'Leeds': 'Leeds United', 'Sheffield United': 'Sheffield Utd',
    'West Ham': 'West Ham United', 'Wolves': 'Wolverhampton',
    'Brighton': 'Brighton', 'Huddersfield': 'Huddersfield',
    'Cardiff': 'Cardiff City', 'Swansea': 'Swansea City',
    'Stoke': 'Stoke City', 'Hull': 'Hull City',
    'QPR': 'QPR', 'West Brom': 'West Brom',
    'Bournemouth': 'Bournemouth', "Nott'm Forest": 'Nott. Forest',
    'Luton': 'Luton', 'Ipswich': 'Ipswich',
}

def normalize_name(name):
    if not isinstance(name, str): return name
    name = name.strip()
    return TEAM_MAPPING.get(name, name)

def main():
    print("🚀 Premier League Feature Engineering Pipeline")
    print("=" * 60)

    # === 1. LOAD ALL SEASONS ===
    files = sorted(glob.glob(os.path.join(DATA_DIR, "E0-*.csv")))
    print(f"\n📂 Found {len(files)} season files.")

    all_matches = []
    for f in files:
        try:
            df = pd.read_csv(f, encoding='latin1')
            base_cols = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']
            if not all(c in df.columns for c in base_cols):
                print(f"  ⚠️ Skipping {os.path.basename(f)}: Missing columns.")
                continue

            shot_cols = ['HS', 'AS', 'HST', 'AST']
            available_shot_cols = [c for c in shot_cols if c in df.columns]
            df = df[base_cols + available_shot_cols].dropna(subset=base_cols)

            # Extract season from filename (E0-2024-25.csv -> 2024)
            basename = os.path.basename(f)
            try:
                season_year = int(basename.split('-')[1])
            except (IndexError, ValueError):
                season_year = 2020
            df['Season'] = season_year

            all_matches.append(df)
            print(f"   → {basename}: {len(df)} matches")
        except Exception as e:
            print(f"  ❌ Error {os.path.basename(f)}: {e}")

    df = pd.concat(all_matches, ignore_index=True)
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)

    # Normalize team names
    df['HomeTeam'] = df['HomeTeam'].apply(normalize_name)
    df['AwayTeam'] = df['AwayTeam'].apply(normalize_name)

    # Ensure numeric
    for c in ['FTHG', 'FTAG', 'HS', 'AS', 'HST', 'AST']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    print(f"\n📊 Total: {len(df)} matches, {df['HomeTeam'].nunique()} teams")
    print(f"   Date range: {df['Date'].min().date()} → {df['Date'].max().date()}")

    # === 2. xG PROXY ===
    print("\n⚙️ Computing xG Proxy...")
    if 'HST' in df.columns:
        df['Home_xG'] = df['HST'] * 0.35 + df.get('HS', df['HST']) * 0.10
        df['Away_xG'] = df['AST'] * 0.35 + df.get('AS', df['AST']) * 0.10
    else:
        df['Home_xG'] = df['FTHG'] * 0.9
        df['Away_xG'] = df['FTAG'] * 0.9

    # === 3. PRESSURE PROXY (PPDA) ===
    print("⚙️ Computing Pressure Proxy...")
    if 'HS' in df.columns:
        df['Home_Pressure'] = (df['HS'] + df['HST']) / (df['AS'] + df['AST'] + 1)
        df['Away_Pressure'] = (df['AS'] + df['AST']) / (df['HS'] + df['HST'] + 1)
    else:
        df['Home_Pressure'] = 1.0
        df['Away_Pressure'] = 1.0

    # === 4. ELO RATINGS ===
    print("⚙️ Computing Elo Ratings...")
    elo = {}
    K = 20
    home_elo_list, away_elo_list = [], []

    for _, row in df.iterrows():
        h, a = row['HomeTeam'], row['AwayTeam']
        rh = elo.get(h, 1500.0)
        ra = elo.get(a, 1500.0)
        home_elo_list.append(rh)
        away_elo_list.append(ra)

        eh = 1 / (1 + 10 ** ((ra - rh) / 400))
        ea = 1 - eh

        if row['FTR'] == 'H':
            sh, sa = 1, 0
        elif row['FTR'] == 'A':
            sh, sa = 0, 1
        else:
            sh, sa = 0.5, 0.5

        elo[h] = rh + K * (sh - eh)
        elo[a] = ra + K * (sa - ea)

    df['Home_Elo'] = home_elo_list
    df['Away_Elo'] = away_elo_list

    # === 5. ROLLING FEATURES (L5) ===
    print("⚙️ Computing Rolling Features (L5)...")
    teams = set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())

    for col in ['xG_Avg_L5', 'Streak_L5', 'Pressure_Avg_L5']:
        df[f'Home_{col}'] = np.nan
        df[f'Away_{col}'] = np.nan

    for team in teams:
        mask_home = df['HomeTeam'] == team
        mask_away = df['AwayTeam'] == team

        # Build per-team series in chronological order
        idxs = df.index[mask_home | mask_away].tolist()
        xg_vals, pts_vals, press_vals = [], [], []

        for idx in idxs:
            row = df.loc[idx]
            is_home = row['HomeTeam'] == team

            # xG
            xg = row['Home_xG'] if is_home else row['Away_xG']
            xg_vals.append(xg)

            # Points (streak)
            if is_home:
                pts = 3 if row['FTR'] == 'H' else (1 if row['FTR'] == 'D' else 0)
            else:
                pts = 3 if row['FTR'] == 'A' else (1 if row['FTR'] == 'D' else 0)
            pts_vals.append(pts)

            # Pressure
            press = row['Home_Pressure'] if is_home else row['Away_Pressure']
            press_vals.append(press)

        # Compute rolling averages (shifted to prevent leakage)
        xg_series = pd.Series(xg_vals, index=idxs)
        pts_series = pd.Series(pts_vals, index=idxs)
        press_series = pd.Series(press_vals, index=idxs)

        xg_roll = xg_series.shift(1).rolling(5, min_periods=1).mean()
        pts_roll = pts_series.shift(1).rolling(5, min_periods=1).mean()
        press_roll = press_series.shift(1).rolling(5, min_periods=1).mean()

        for i, idx in enumerate(idxs):
            row = df.loc[idx]
            is_home = row['HomeTeam'] == team
            prefix = 'Home' if is_home else 'Away'

            df.at[idx, f'{prefix}_xG_Avg_L5'] = xg_roll.iloc[i]
            df.at[idx, f'{prefix}_Streak_L5'] = pts_roll.iloc[i]
            df.at[idx, f'{prefix}_Pressure_Avg_L5'] = press_roll.iloc[i]

    # === 6. DOMINANCE ===
    print("⚙️ Computing Dominance...")
    df['Home_Dominance'] = (
        df['Home_Elo'] / 1500 * 0.4 +
        df['Home_xG_Avg_L5'].fillna(0) * 0.3 +
        df['Home_Streak_L5'].fillna(0) / 3 * 0.3
    )
    df['Away_Dominance'] = (
        df['Away_Elo'] / 1500 * 0.4 +
        df['Away_xG_Avg_L5'].fillna(0) * 0.3 +
        df['Away_Streak_L5'].fillna(0) / 3 * 0.3
    )

    # === 7. SELECT & EXPORT ===
    export_cols = [
        'Date', 'Season', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR',
        'Home_Elo', 'Away_Elo',
        'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
        'Home_Streak_L5', 'Away_Streak_L5',
        'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
        'Home_Dominance', 'Away_Dominance'
    ]

    df_export = df[export_cols].copy()
    df_export = df_export.fillna(0)

    df_export.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved to: {OUTPUT_FILE}")
    print(f"   Shape: {df_export.shape}")
    print(f"   NaN check: {df_export.isna().sum().sum()}")
    print("\n✅ Pipeline Complete!")

if __name__ == '__main__':
    main()
