import pandas as pd
import numpy as np
import json
import os

# === PATHS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATCHES_FILE = os.path.join(BASE_DIR, '../data/processed/matches_raw.csv')
FIFA_FILE = os.path.join(BASE_DIR, '../data/processed/fifa_ratings_raw.json')
MARKET_FILE = os.path.join(BASE_DIR, '../data/processed/market_values_raw.json')
OUTPUT_FILE = os.path.join(BASE_DIR, '../data/processed/df_premier_complete.csv')

# === CONFIG ===
# Columns Sequence
FINAL_COLS = [
    'Date','Home_Team','Away_Team','Home_Goals','Away_Goals','FTR',
    'Home_Elo','Away_Elo','Home_Att_Strength','Away_Att_Strength',
    'Home_Def_Weakness','Away_Def_Weakness',
    'Home_FIFA_Ova','Away_FIFA_Ova','Home_Market_Value','Away_Market_Value',
    'Home_xG_Avg_L5','Away_xG_Avg_L5','Home_Streak_L5','Away_Streak_L5',
    'Home_H2H_L3','Away_H2H_L3','Home_Pressure_Avg_L5','Away_Pressure_Avg_L5',
    'Home_Goal_Diff_L5','Away_Goal_Diff_L5','Home_Rest_Days','Away_Rest_Days'
]

def get_season_year(date):
    # Returns the 'start year' of the season (e.g. Aug 2023 -> 2023, Jan 2024 -> 2023)
    # Cutoff usually July
    if date.month > 7: return date.year
    return date.year - 1

# === MAPPINGS ===
# Map scraped names (SoFIFA/TM) to our Match Data names
SCRAPED_MAPPING = {
    'Manchester United': 'Man United', 'Manchester City': 'Man City',
    'Tottenham Hotspur': 'Tottenham', 'Newcastle United': 'Newcastle',
    'Leicester City': 'Leicester', 'Norwich City': 'Norwich',
    'Leeds United': 'Leeds', 'Sheffield United': 'Sheffield United',
    'West Ham United': 'West Ham', 'Wolverhampton Wanderers': 'Wolves',
    'Brighton & Hove Albion': 'Brighton', 'Huddersfield Town': 'Huddersfield',
    'Cardiff City': 'Cardiff', 'Swansea City': 'Swansea',
    'Stoke City': 'Stoke', 'Hull City': 'Hull',
    'Queens Park Rangers': 'QPR', 'West Bromwich Albion': 'West Brom',
    'AFC Bournemouth': 'Bournemouth', 'Nottingham Forest': "Nott'm Forest",
    'Luton Town': 'Luton', 'Ipswich Town': 'Ipswich',
    'Arsenal FC': 'Arsenal', 'Chelsea FC': 'Chelsea', 'Liverpool FC': 'Liverpool',
    'Everton FC': 'Everton', 'Fulham FC': 'Fulham', 'Sunderland AFC': 'Sunderland',
    'Wigan Athletic': 'Wigan', 'Bolton Wanderers': 'Bolton', 'Blackburn Rovers': 'Blackburn',
    'Birmingham City': 'Birmingham', 'Blackpool FC': 'Blackpool', 'Southampton FC': 'Southampton',
    'Watford FC': 'Watford', 'Burnley FC': 'Burnley', 'Brentford FC': 'Brentford'
}

def parse_market_value(val_str):
    if isinstance(val_str, (int, float)): return val_str
    if not isinstance(val_str, str): return 0
    
    clean = val_str.replace('€', '').replace('£', '').strip()
    factor = 1.0
    
    if 'bn' in clean:
        factor = 1000.0
        clean = clean.replace('bn', '')
    elif 'm' in clean:
        factor = 1.0
        clean = clean.replace('m', '')
    elif 'k' in clean:
        factor = 0.001
        clean = clean.replace('k', '')
        
    try:
        return float(clean) * factor
    except:
        return 0

def get_interpolated_value(data_dict, team, year):
    # Try exact match
    team_norm = team # Assume match data team name is standard
    
    # 1. Check exact year
    if year in data_dict:
        # Check keys in that year (normalize them)
        year_data = data_dict[year]
        # Create normalized map for this year
        norm_year_data = {SCRAPED_MAPPING.get(k, k): v for k, v in year_data.items()}
        
        if team_norm in norm_year_data:
            return norm_year_data[team_norm]
            
    # 2. If not found, find nearest years
    years = sorted([int(y) for y in data_dict.keys()])
    target = int(year)
    
    # Find closest year available
    closest_year = min(years, key=lambda x: abs(x - target))
    
    # Get value from closest
    c_data = data_dict[str(closest_year)]
    c_norm = {SCRAPED_MAPPING.get(k, k): v for k, v in c_data.items()}
    
    if team_norm in c_norm:
        return c_norm[team_norm]
        
    return None # Not found in any year

def load_json_safe(path):
    if not os.path.exists(path):
        print(f"⚠️ Warning: {path} not found. Using empty dict.")
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_elo(df):
    # Basic Elo implementation
    elo_dict = {team: 1500 for team in pd.concat([df['Home_Team'], df['Away_Team']]).unique()}
    k_factor = 32
    
    home_elos = []
    away_elos = []
    
    for _, row in df.iterrows():
        h, a = row['Home_Team'], row['Away_Team']
        r_h = elo_dict[h]
        r_a = elo_dict[a]
        
        home_elos.append(r_h)
        away_elos.append(r_a)
        
        # Result
        if row['FTR'] == 'H': result = 1
        elif row['FTR'] == 'A': result = 0
        else: result = 0.5
        
        # Expectation
        e_h = 1 / (1 + 10 ** ((r_a - r_h) / 400))
        
        # Update
        new_rating_h = r_h + k_factor * (result - e_h)
        new_rating_a = r_a + k_factor * ((1-result) - (1-e_h))
        
        elo_dict[h] = new_rating_h
        elo_dict[a] = new_rating_a
        
    df['Home_Elo'] = home_elos
    df['Away_Elo'] = away_elos
    return df

def main():
    print("🚀 Starting Dataset Consolidation...")
    
    # 1. Load Data
    if not os.path.exists(MATCHES_FILE):
        print("❌ Matches file not found. Run clean_matches.py first.")
        return
        
    df = pd.read_csv(MATCHES_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    
    fifa_data = load_json_safe(FIFA_FILE)
    market_data = load_json_safe(MARKET_FILE)
    
    print(f"📊 Loaded {len(df)} matches.")
    
    # 2. Add Base Columns
    df = df.rename(columns={'HomeTeam': 'Home_Team', 'AwayTeam': 'Away_Team', 'FTHG': 'Home_Goals', 'FTAG': 'Away_Goals'})
    
    # xG Proxy
    if 'HS' in df.columns and 'HST' in df.columns:
        df['Home_xG'] = (df['HS'] * 0.05) + (df['HST'] * 0.2)
        df['Away_xG'] = (df['AS'] * 0.05) + (df['AST'] * 0.2)
    else:
        df['Home_xG'] = df['Home_Goals'] * 0.8 + 0.2
        df['Away_xG'] = df['Away_Goals'] * 0.8 + 0.2
        
    # Pressure Proxy
    if 'HC' in df.columns:
        total_c = df['HC'] + df['AC']
        df['Home_Pressure'] = (df['HC'] / total_c * 100).fillna(50)
        df['Away_Pressure'] = (df['AC'] / total_c * 100).fillna(50)
    else:
        df['Home_Pressure'] = 50
        df['Away_Pressure'] = 50

    # 3. Aux Data Mapping
    print("⚙️ Mapping FIFA & Market Values (with interpolation)...")
    h_fifa, a_fifa = [], []
    h_mv, a_mv = [], []
    
    for _, row in df.iterrows():
        year = str(get_season_year(row['Date']))
        
        # FIFA
        val_h = get_interpolated_value(fifa_data, row['Home_Team'], year)
        val_a = get_interpolated_value(fifa_data, row['Away_Team'], year)
        h_fifa.append(val_h if val_h else 75)
        a_fifa.append(val_a if val_a else 75)
        
        # Market Value
        raw_h = get_interpolated_value(market_data, row['Home_Team'], year)
        raw_a = get_interpolated_value(market_data, row['Away_Team'], year)
        
        h_mv.append(parse_market_value(raw_h) if raw_h else 100)
        a_mv.append(parse_market_value(raw_a) if raw_a else 100)
        
    df['Home_FIFA_Ova'] = h_fifa
    df['Away_FIFA_Ova'] = a_fifa
    df['Home_Market_Value'] = h_mv
    df['Away_Market_Value'] = a_mv
    
    # 4. Elo Calculation
    print("⚙️ Calculating Elo...")
    df = calculate_elo(df)
    
    # 5. Rolling Features
    print("⚙️ generating Rolling Features (L5/L10/H2H)...")
    
    # Pre-calculate dictionaries for speed
    # We'll stick to a simple iterative approach for correctness over vectorization for specific logical windows
    
    stats = {} # {team: {goals_scored: [], goals_conceded: [], xg: [], points: [], pressure: [], last_date: date}}
    h2h = {} # {(t1, t2): [points]}
    
    # Result Lists
    h_att, a_att = [], []
    h_def, a_def = [], []
    h_xg, a_xg = [], []
    h_str, a_str = [], []
    h_h2h, a_h2h = [], []
    h_press, a_press = [], []
    h_gd, a_gd = [], []
    h_rest, a_rest = [], []
    
    for idx, row in df.iterrows():
        h, a = row['Home_Team'], row['Away_Team']
        date = row['Date']
        
        # Init stats if new
        if h not in stats: stats[h] = {'gf':[], 'ga':[], 'xg':[], 'pts':[], 'press':[], 'date': None}
        if a not in stats: stats[a] = {'gf':[], 'ga':[], 'xg':[], 'pts':[], 'press':[], 'date': None}
        
        # --- GET PRE-MATCH FEATURES (Past Data) ---
        
        # 1. Att/Def Strength (L10)
        # Avg goals scored/conceded L10
        h_att.append(np.mean(stats[h]['gf'][-10:]) if stats[h]['gf'] else 1.0)
        a_att.append(np.mean(stats[a]['gf'][-10:]) if stats[a]['gf'] else 1.0)
        h_def.append(np.mean(stats[h]['ga'][-10:]) if stats[h]['ga'] else 1.0)
        a_def.append(np.mean(stats[a]['ga'][-10:]) if stats[a]['ga'] else 1.0)
        
        # 2. xG (L5)
        h_xg.append(np.mean(stats[h]['xg'][-5:]) if stats[h]['xg'] else 1.0)
        a_xg.append(np.mean(stats[a]['xg'][-5:]) if stats[a]['xg'] else 1.0)
        
        # 3. Streak (L5 Points sum)
        h_str.append(sum(stats[h]['pts'][-5:]))
        a_str.append(sum(stats[a]['pts'][-5:]))
        
        # 4. Pressure (L5)
        h_press.append(np.mean(stats[h]['press'][-5:]) if stats[h]['press'] else 50)
        a_press.append(np.mean(stats[a]['press'][-5:]) if stats[a]['press'] else 50)
        
        # 5. Goal Diff (L5)
        h_gd_val = sum(stats[h]['gf'][-5:]) - sum(stats[h]['ga'][-5:])
        a_gd_val = sum(stats[a]['gf'][-5:]) - sum(stats[a]['ga'][-5:])
        h_gd.append(h_gd_val)
        a_gd.append(a_gd_val)
        
        # 6. Rest Days
        last_h = stats[h]['date']
        last_a = stats[a]['date']
        h_rest.append((date - last_h).days if last_h else 7)
        a_rest.append((date - last_a).days if last_a else 7)
        
        # 7. H2H (L3)
        pair = tuple(sorted([h, a]))
        if pair not in h2h: h2h[pair] = []
        
        # Calculate points from past H2H for Home and Away perspective
        # stored as (team, points) tuple list? No, simpler: stored as list of results relative to 'h' (sorted[0])?
        # Let's just store list of objects: {'team': 'Arsenal', 'pts': 3}
        
        h_pts_h2h = 0
        a_pts_h2h = 0
        # Filter last 3 games involving these two
        past_games = h2h[pair][-3:]
        for g in past_games:
            if g['team'] == h: h_pts_h2h += g['pts']
            if g['team'] == a: a_pts_h2h += g['pts']
            
        h_h2h.append(h_pts_h2h)
        a_h2h.append(a_pts_h2h)
        
        
        # --- UPDATE STATS (Post-Match) ---
        hg, ag = row['Home_Goals'], row['Away_Goals']
        
        # Points
        h_p = 3 if hg > ag else (1 if hg == ag else 0)
        a_p = 3 if ag > hg else (1 if ag == hg else 0)
        
        # Update Home
        stats[h]['gf'].append(hg)
        stats[h]['ga'].append(ag)
        stats[h]['xg'].append(row['Home_xG'])
        stats[h]['pts'].append(h_p)
        stats[h]['press'].append(row['Home_Pressure'])
        stats[h]['date'] = date
        
        # Update Away
        stats[a]['gf'].append(ag)
        stats[a]['ga'].append(hg)
        stats[a]['xg'].append(row['Away_xG'])
        stats[a]['pts'].append(a_p)
        stats[a]['press'].append(row['Away_Pressure'])
        stats[a]['date'] = date
        
        # Update H2H
        h2h[pair].append({'team': h, 'pts': h_p})
        h2h[pair].append({'team': a, 'pts': a_p})
        
    # Assign new cols
    df['Home_Att_Strength'] = h_att
    df['Away_Att_Strength'] = a_att
    df['Home_Def_Weakness'] = h_def
    df['Away_Def_Weakness'] = a_def
    df['Home_xG_Avg_L5'] = h_xg
    df['Away_xG_Avg_L5'] = a_xg
    df['Home_Streak_L5'] = h_str
    df['Away_Streak_L5'] = a_str
    df['Home_H2H_L3'] = h_h2h
    df['Away_H2H_L3'] = a_h2h
    df['Home_Pressure_Avg_L5'] = h_press
    df['Away_Pressure_Avg_L5'] = a_press
    df['Home_Goal_Diff_L5'] = h_gd
    df['Away_Goal_Diff_L5'] = a_gd
    df['Home_Rest_Days'] = h_rest
    df['Away_Rest_Days'] = a_rest
    
    # 6. Final Clean & Save
    df_final = df[FINAL_COLS].copy()
    
    # Round floats
    cols_float = df_final.select_dtypes(include=['float']).columns
    df_final[cols_float] = df_final[cols_float].round(3)
    
    print(f"💾 Saving complete dataset to {OUTPUT_FILE}...")
    df_final.to_csv(OUTPUT_FILE, index=False)
    print("✅ Done!")

if __name__ == "__main__":
    main()
