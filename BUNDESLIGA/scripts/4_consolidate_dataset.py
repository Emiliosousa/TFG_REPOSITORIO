import pandas as pd
import numpy as np
import json
import os
import unicodedata

# === PATHS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATCHES_FILE = os.path.join(BASE_DIR, '../data/processed/matches_raw.csv')
FIFA_FILE = os.path.join(BASE_DIR, '../data/processed/fifa_ratings_raw.json')
MARKET_FILE = os.path.join(BASE_DIR, '../data/processed/market_values_raw.json')
OUTPUT_FILE = os.path.join(BASE_DIR, '../data/processed/df_final_clean.csv')

# === CONFIG ===
FINAL_COLS = [
    'Date','Season', 'HomeTeam','AwayTeam','FTHG','FTAG','FTR', 'Target',
    'B365H', 'B365D', 'B365A', 'MaxH', 'MaxD', 'MaxA',
    'Home_Elo','Away_Elo',
    'Home_FIFA_Ova','Away_FIFA_Ova','Home_Market_Value','Away_Market_Value',
    'Home_xG_Avg_L5','Away_xG_Avg_L5','Home_Streak_L5','Away_Streak_L5',
    'Home_Pressure_Avg_L5','Away_Pressure_Avg_L5'
]

def get_season_year(date):
    if date.month > 7: return date.year
    return date.year - 1

def normalize_string(s):
    if not isinstance(s, str): return ""
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    return s.lower().replace(' ', '').replace('.', '').replace('-', '')

TEAM_ALIASES = {
    'bayernmunich': 'Bayern Munich', 'fcbayernmunchen': 'Bayern Munich',
    'borussiadortmund': 'Borussia Dortmund', 'dortmund': 'Borussia Dortmund',
    'bayer04leverkusen': 'Bayer Leverkusen', 'bayerleverkusen': 'Bayer Leverkusen',
    'rbleipzig': 'RB Leipzig', 'leipzig': 'RB Leipzig',
    'borussiamonchengladbach': 'Borussia Monchengladbach', 'mgladbach': 'Borussia Monchengladbach',
    'vflwolfsburg': 'VfL Wolfsburg', 'wolfsburg': 'VfL Wolfsburg',
    'eintrachtfrankfurt': 'Eintracht Frankfurt', 'frankfurt': 'Eintracht Frankfurt',
    'tsghoffenheim': 'TSG Hoffenheim', 'hoffenheim': 'TSG Hoffenheim',
    'scfreiburg': 'SC Freiburg', 'freiburg': 'SC Freiburg',
    'werderbremen': 'Werder Bremen', 'svwerderbremen': 'Werder Bremen',
    'fsvmainz05': 'FSV Mainz 05', 'mainz': 'FSV Mainz 05', '1fsvmainz05': 'FSV Mainz 05',
    'unionberlin': 'Union Berlin', '1fcunionberlin': 'Union Berlin',
    'fccologne': 'FC Cologne', '1fckoln': 'FC Cologne', 'koln': 'FC Cologne',
    'fcschalke04': 'FC Schalke 04', 'schalke04': 'FC Schalke 04',
    'vfbstuttgart': 'VfB Stuttgart', 'stuttgart': 'VfB Stuttgart',
    'fcaugsburg': 'FC Augsburg', 'augsburg': 'FC Augsburg',
    'vflbochum': 'VfL Bochum', 'vflbochum1848': 'VfL Bochum', 'bochum': 'VfL Bochum',
    'herthabsc': 'Hertha BSC', 'hertha': 'Hertha BSC', 'herthaberlin': 'Hertha BSC',
    'arminiabielefeld': 'Arminia Bielefeld', 'dscarminiabielefeld': 'Arminia Bielefeld', 'bielefeld': 'Arminia Bielefeld',
    'svdarmstadt98': 'SV Darmstadt 98', 'darmstadt': 'SV Darmstadt 98',
    'fortunadusseldorf': 'Fortuna Dusseldorf', 'dusseldorf': 'Fortuna Dusseldorf',
    'hannover96': 'Hannover 96', 'hannover': 'Hannover 96',
    '1fcnurnberg': 'FC Nurnberg', 'nurnberg': 'FC Nurnberg', 'fcnurnberg': 'FC Nurnberg',
    'scpaderborn07': 'SC Paderborn 07', 'paderborn': 'SC Paderborn 07',
    'greutherfurth': 'Greuther Furth', 'spvgggreutherfurth': 'Greuther Furth',
    'hamburgersv': 'Hamburger SV', 'hamburg': 'Hamburger SV',
    'fcstpauli': 'FC St. Pauli', 'stpauli': 'FC St. Pauli',
    '1fcheidenheim1846': '1. FC Heidenheim', '1fcheidenheim': '1. FC Heidenheim', 'heidenheim': '1. FC Heidenheim',
    'holsteinkiel': 'Holstein Kiel', 'kiel': 'Holstein Kiel'
}

def resolve_team(raw_name):
    n = normalize_string(raw_name)
    return TEAM_ALIASES.get(n, raw_name)

def parse_market_value(val_str):
    if isinstance(val_str, (int, float)): return val_str
    if not isinstance(val_str, str): return 0
    clean = val_str.replace('€', '').replace('£', '').strip()
    factor = 1.0
    if 'bn' in clean: factor = 1000.0; clean = clean.replace('bn', '')
    elif 'm' in clean: factor = 1.0; clean = clean.replace('m', '')
    elif 'k' in clean: factor = 0.001; clean = clean.replace('k', '')
    try: return float(clean) * factor
    except: return 0

def get_interpolated_value(data_dict, team, year):
    target = int(year)
    years = sorted([int(y) for y in data_dict.keys()])
    if not years: return None
    
    closest_year = min(years, key=lambda x: abs(x - target))
    year_data = data_dict[str(closest_year)]
    
    norm_data = {resolve_team(k): v for k, v in year_data.items()}
    if team in norm_data:
        return norm_data[team]
    return None

def calculate_elo(df):
    elo_dict = {team: 1500 for team in pd.concat([df['HomeTeam'], df['AwayTeam']]).unique()}
    k_factor = 32
    home_elos, away_elos = [], []
    for _, row in df.iterrows():
        h, a = row['HomeTeam'], row['AwayTeam']
        r_h, r_a = elo_dict[h], elo_dict[a]
        home_elos.append(r_h)
        away_elos.append(r_a)
        
        result = 1 if row['FTR'] == 'H' else (0 if row['FTR'] == 'A' else 0.5)
        e_h = 1 / (1 + 10 ** ((r_a - r_h) / 400))
        
        elo_dict[h] = r_h + k_factor * (result - e_h)
        elo_dict[a] = r_a + k_factor * ((1-result) - (1-e_h))
        
    df['Home_Elo'] = home_elos
    df['Away_Elo'] = away_elos
    return df

def main():
    print("🚀 Starting Bundesliga Data Consolidation...")
    
    if not os.path.exists(MATCHES_FILE):
        print("❌ Matches file not found.")
        return
        
    df = pd.read_csv(MATCHES_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    
    df['Season'] = df['Date'].apply(get_season_year)
    df['Target'] = df['FTR'].map({'A': 0, 'D': 1, 'H': 2})
    
    fifa_data = {}
    market_data = {}
    if os.path.exists(FIFA_FILE):
        with open(FIFA_FILE, 'r') as f: fifa_data = json.load(f)
    if os.path.exists(MARKET_FILE):
        with open(MARKET_FILE, 'r') as f: market_data = json.load(f)

    # Basic feature engineering natively to save steps
    # We must check if the value is na because football-data.co.uk retains the column but leaves it empty for older seasons.
    if 'HS' in df.columns and 'HST' in df.columns:
        df['Home_xG'] = np.where(df['HS'].notna(), (df['HS'] * 0.05) + (df['HST'] * 0.2), df['FTHG'] * 0.8 + 0.2)
        df['Away_xG'] = np.where(df['AS'].notna(), (df['AS'] * 0.05) + (df['AST'] * 0.2), df['FTAG'] * 0.8 + 0.2)
    else:
        df['Home_xG'] = df['FTHG'] * 0.8 + 0.2
        df['Away_xG'] = df['FTAG'] * 0.8 + 0.2
        
    if 'HC' in df.columns and 'AC' in df.columns:
        total_c = df['HC'] + df['AC']
        df['Home_Pressure'] = np.where(df['HC'].notna(), (df['HC'] / np.where(total_c==0, 1, total_c) * 100), 50.0)
        df['Away_Pressure'] = np.where(df['AC'].notna(), (df['AC'] / np.where(total_c==0, 1, total_c) * 100), 50.0)
    else:
        df['Home_Pressure'] = 50.0
        df['Away_Pressure'] = 50.0

    h_fifa, a_fifa, h_mv, a_mv = [], [], [], []
    for _, row in df.iterrows():
        year = str(row['Season'])
        v_h_f = get_interpolated_value(fifa_data, row['HomeTeam'], year)
        v_a_f = get_interpolated_value(fifa_data, row['AwayTeam'], year)
        h_fifa.append(v_h_f if v_h_f else 75)
        a_fifa.append(v_a_f if v_a_f else 75)
        
        v_h_m = get_interpolated_value(market_data, row['HomeTeam'], year)
        v_a_m = get_interpolated_value(market_data, row['AwayTeam'], year)
        h_mv.append(parse_market_value(v_h_m) if v_h_m else 100)
        a_mv.append(parse_market_value(v_a_m) if v_a_m else 100)
        
    df['Home_FIFA_Ova'] = h_fifa
    df['Away_FIFA_Ova'] = a_fifa
    df['Home_Market_Value'] = h_mv
    df['Away_Market_Value'] = a_mv
    
    df = calculate_elo(df)
    
    # Rolling Features Logic (Rolling averages)
    stats = {}
    h_xg, a_xg, h_str, a_str, h_press, a_press = [], [], [], [], [], []
    
    for idx, row in df.iterrows():
        h, a = row['HomeTeam'], row['AwayTeam']
        if h not in stats: stats[h] = {'xg':[], 'pts':[], 'press':[]}
        if a not in stats: stats[a] = {'xg':[], 'pts':[], 'press':[]}
        
        h_xg.append(np.mean(stats[h]['xg'][-5:]) if len(stats[h]['xg'])>0 else 1.0)
        a_xg.append(np.mean(stats[a]['xg'][-5:]) if len(stats[a]['xg'])>0 else 1.0)
        
        h_str.append(sum(stats[h]['pts'][-5:]))
        a_str.append(sum(stats[a]['pts'][-5:]))
        
        h_press.append(np.mean(stats[h]['press'][-5:]) if len(stats[h]['press'])>0 else 50.0)
        a_press.append(np.mean(stats[a]['press'][-5:]) if len(stats[a]['press'])>0 else 50.0)
        
        # update stats
        hg, ag = row['FTHG'], row['FTAG']
        hp = 3 if hg > ag else (1 if hg == ag else 0)
        ap = 3 if ag > hg else (1 if ag == hg else 0)
        
        stats[h]['xg'].append(row['Home_xG'])
        stats[h]['pts'].append(hp)
        stats[h]['press'].append(row['Home_Pressure'])
        
        stats[a]['xg'].append(row['Away_xG'])
        stats[a]['pts'].append(ap)
        stats[a]['press'].append(row['Away_Pressure'])
        
    df['Home_xG_Avg_L5'] = h_xg
    df['Away_xG_Avg_L5'] = a_xg
    df['Home_Streak_L5'] = h_str
    df['Away_Streak_L5'] = a_str
    df['Home_Pressure_Avg_L5'] = h_press
    df['Away_Pressure_Avg_L5'] = a_press
    
    # Make sure we don't save matches without odds since we need them to calculate EV
    df = df.dropna(subset=['B365H', 'B365D', 'B365A']).copy()
    
    # Fill Max odds with B365 if missing (fallback for older matches without Max odds tracking)
    for max_col, b365_col in zip(['MaxH', 'MaxD', 'MaxA'], ['B365H', 'B365D', 'B365A']):
        if max_col in df.columns:
            df[max_col] = df[max_col].fillna(df[b365_col])
        else:
            df[max_col] = df[b365_col]
    
    # Build final df
    df_final = df[[c for c in FINAL_COLS if c in df.columns]].copy()
    
    print(f"💾 Saving complete dataset to {OUTPUT_FILE}...")
    df_final.to_csv(OUTPUT_FILE, index=False)
    print("✅ Done!")

if __name__ == "__main__":
    main()
