import json

notebook_path = '02_Modelado_Avanzado_Academic_v2.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb.get('cells', []):
    if cell.get('cell_type') == 'code':
        source = cell.get('source', [])
        
        for i, line in enumerate(source):
            if 'target_map = {"A": 0, "D": 1, "H": 2}\\n' in repr(line):
                # We will insert the float season fix right after target mapping
                # But since it's easier to just replace, let's do simple replaces.
                pass
        
        # A safer way to replace on the full text
        full_text = "".join(source)
        
        
        full_text = full_text.replace(
            'df["Target"] = df["FTR"].map(target_map)\n\n# ===========================================================',
            'df["Target"] = df["FTR"].map(target_map)\ndf["Season"] = df["Season"].fillna(df["Date"].apply(lambda d: d.year if d.month >= 8 else d.year - 1))\ndf["Season"] = df["Season"].astype(int)\n\n# ==========================================================='
        )
        
        # remove the old season fix block
        old_fix_block = '''df.head()

# Season fix: fill NaN seasons based on date
if df["Season"].isna().any():
    df["Date"] = pd.to_datetime(df["Date"])
    mask = df["Season"].isna()
    df.loc[mask, "Season"] = df.loc[mask, "Date"].apply(lambda d: d.year if d.month >= 8 else d.year - 1)
    df["Season"] = df["Season"].astype(int)
    print(f"Fixed {mask.sum()} rows with NaN Season")
'''
        full_text = full_text.replace(old_fix_block, "df.head()\n")
        
        # fix features assignment
        bad_features_block = '''# Re-assign to global X, y, season_series
features = [
    "Home_Elo", "Away_Elo",
    "Home_xG_Avg_L5", "Away_xG_Avg_L5",
    "Home_Streak_L5", "Away_Streak_L5",
    "Home_Pressure_Avg_L5", "Away_Pressure_Avg_L5",
    "Home_Dominance_Avg_L5", "Away_Dominance_Avg_L5",
    "Home_FIFA_Ova", "Away_FIFA_Ova",
    "Home_Market_Value", "Away_Market_Value",
    "Home_Att_Strength", "Away_Att_Strength",
    "Home_Def_Weakness", "Away_Def_Weakness",
    "Home_H2H_L3", "Away_H2H_L3",
    "Home_Rest_Days", "Away_Rest_Days"
]
# Filter to only features that exist in df
features = [f for f in features if f in df.columns]
# Filter to only features that exist in df
features = [
    "Home_Elo", "Away_Elo",
    "Home_xG_Avg_L5", "Away_xG_Avg_L5",
    "Home_Streak_L5", "Away_Streak_L5",
    "Home_Pressure_Avg_L5", "Away_Pressure_Avg_L5",
    "Home_Dominance_Avg_L5", "Away_Dominance_Avg_L5",
    "Home_FIFA_Ova", "Away_FIFA_Ova",
    "Home_Market_Value", "Away_Market_Value",
    "Home_Att_Strength", "Away_Att_Strength",
    "Home_Def_Weakness", "Away_Def_Weakness",
    "Home_H2H_L3", "Away_H2H_L3",
    "Home_Rest_Days", "Away_Rest_Days"
]
# Filter to only features that exist in df
features = [f for f in features if f in df.columns]'''
        good_features_block = '''features = [
    "Home_Elo", "Away_Elo",
    "Home_xG_Avg_L5", "Away_xG_Avg_L5",
    "Home_Streak_L5", "Away_Streak_L5",
    "Home_Pressure_Avg_L5", "Away_Pressure_Avg_L5",
    "Home_Dominance_Avg_L5", "Away_Dominance_Avg_L5",
    "Home_FIFA_OVR", "Away_FIFA_OVR",
    "Home_TM_Value", "Away_TM_Value",
    "Home_TM_Avg_Age", "Away_TM_Avg_Age"
]
# Filter to only features that exist in df
features = [f for f in features if f in df.columns]'''
        full_text = full_text.replace(bad_features_block, good_features_block)
        
        # fix objective function walk-forward and odds
        old_val_block = '''    unique_seasons = sorted(season_series.unique())
    
    # Start validation from 6th season (need history to stabilize)
    for i in range(5, len(unique_seasons)):
        train_seasons = unique_seasons[:i]
        val_season = unique_seasons[i]
        
        train_mask = season_series.isin(train_seasons)
        val_mask = season_series == val_season
        
        X_train, y_train = X[train_mask], y[train_mask]
        X_val, y_val = X[val_mask], y[val_mask]'''
        
        new_val_block = '''    unique_seasons = sorted(df['Season'].unique())
    
    # Start validation from 6th season (need history to stabilize)
    for i in range(5, len(unique_seasons)):
        train_seasons = unique_seasons[:i]
        val_season = unique_seasons[i]
        
        train_mask = df['Season'].isin(train_seasons)
        val_mask = df['Season'] == val_season
        
        X_train, y_train = df.loc[train_mask, features].astype(float), df.loc[train_mask, 'Target'].astype(int)
        X_val, y_val = df.loc[val_mask, features].astype(float), df.loc[val_mask, 'Target'].astype(int)'''
        full_text = full_text.replace(old_val_block, new_val_block)
        
        old_odds_block = '''        val_indices = X_val.index
        
        # Get Odds
        try:
            val_odds = df_final.loc[val_indices, ['B365A', 'B365D', 'B365H']].values
        except KeyError:'''
        new_odds_block = '''        # Get Odds
        try:
            val_odds = df.loc[val_mask, ['B365A', 'B365D', 'B365H']].values
        except KeyError:'''
        full_text = full_text.replace(old_odds_block, new_odds_block)
        
        full_text = full_text.replace(
            "bet_mask = (best_ev >= 0.10) & (best_odds <= 6.0)",
            "bet_mask = (best_ev >= 0.03) & (best_odds <= 6.0)"
        )
        
        
        # turn back into list of lines
        lines = []
        parts = full_text.split('\n')
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                lines.append(part + '\n')
            else:
                if part:
                    lines.append(part)
        
        cell['source'] = lines

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f)

print("Patching complete.")
