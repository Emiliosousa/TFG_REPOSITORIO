import pandas as pd
import numpy as np
import json
import difflib

df = pd.read_csv('../df_final_app.csv')

with open('../data/sofifa_history.json', 'r', encoding='utf-8') as f: sofifa_data = json.load(f)
with open('../data/transfermarkt_history.json', 'r', encoding='utf-8') as f: tm_data = json.load(f)

def parse_tm_value(val_str):
    if not isinstance(val_str, str): return 0.0
    val_str = val_str.replace('€', '')
    if 'bn' in val_str: return float(val_str.replace('bn', '')) * 1000
    elif 'm' in val_str: return float(val_str.replace('m', ''))
    elif 'Th' in val_str: return float(val_str.replace('Th.', '')) / 1000
    return 0.0

def get_match(name, candidates):
    match = difflib.get_close_matches(name, candidates, n=1, cutoff=0.5)
    return match[0] if match else None

new_cols = [
    'Home_FIFA_OVR', 'Home_FIFA_ATT', 'Home_FIFA_MID', 'Home_FIFA_DEF',
    'Away_FIFA_OVR', 'Away_FIFA_ATT', 'Away_FIFA_MID', 'Away_FIFA_DEF',
    'Home_TM_Value', 'Home_TM_Avg_Age',
    'Away_TM_Value', 'Away_TM_Avg_Age'
]
for c in new_cols: df[c] = np.nan

for season in df['Season'].unique():
    s_str = str(season)
    season_teams = df[df['Season'] == season]['HomeTeam'].unique()
    
    if s_str in sofifa_data:
        fifa_recs = {t['team']: t for t in sofifa_data[s_str]}
        fifa_names = list(fifa_recs.keys())
        
        for team in season_teams:
            match = get_match(team, fifa_names)
            if match:
                data = fifa_recs[match]
                mask_h = (df['Season'] == season) & (df['HomeTeam'] == team)
                df.loc[mask_h, 'Home_FIFA_OVR'] = float(data.get('ova', 0))
                mask_a = (df['Season'] == season) & (df['AwayTeam'] == team)
                df.loc[mask_a, 'Away_FIFA_OVR'] = float(data.get('ova', 0))

    if s_str in tm_data:
        tm_recs = {t['team']: t for t in tm_data[s_str]}
        tm_names = list(tm_recs.keys())
        
        for team in season_teams:
            match = get_match(team, tm_names)
            if match:
                data = tm_recs[match]
                val = parse_tm_value(data.get('value', '0'))
                
                mask_h = (df['Season'] == season) & (df['HomeTeam'] == team)
                df.loc[mask_h, 'Home_TM_Value'] = val
                
                mask_a = (df['Season'] == season) & (df['AwayTeam'] == team)
                df.loc[mask_a, 'Away_TM_Value'] = val

cols_to_check = ['Home_FIFA_OVR', 'Away_FIFA_OVR', 'Home_TM_Value', 'Away_TM_Value']
print("Before ffill/bfill nulls:", df[cols_to_check].isnull().sum())
print("Before ffill/bfill zeros:", (df[cols_to_check] == 0).sum())

df = df.bfill().ffill()
missing_mask = df[cols_to_check].isnull().any(axis=1) | (df[cols_to_check] == 0).any(axis=1)

print('Rows to drop:', missing_mask.sum())
print('Any nulls?', df[cols_to_check].isnull().sum())
print('Any zeros?', (df[cols_to_check] == 0).sum())
