import json

path = 'LaLiga/notebooks/02_Modelado_Avanzado_Academic_v2.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

cell = nb['cells'][4]
lines = cell['source']

# Replace the features block we injected before
new_lines = []
skip_until_bracket = False
for line in lines:
    # Skip the lines we added before
    if 'features = [' in line and '"Home_Elo"' not in line and 'c for c in' not in line:
        skip_until_bracket = True
        # Insert the corrected features using actual column names from df_final_app.csv
        new_lines.append('features = [\n')
        new_lines.append('    "Home_Elo", "Away_Elo",\n')
        new_lines.append('    "Home_xG_Avg_L5", "Away_xG_Avg_L5",\n')
        new_lines.append('    "Home_Streak_L5", "Away_Streak_L5",\n')
        new_lines.append('    "Home_Pressure_Avg_L5", "Away_Pressure_Avg_L5",\n')
        new_lines.append('    "Home_Dominance_Avg_L5", "Away_Dominance_Avg_L5",\n')
        new_lines.append('    "Home_FIFA_Ova", "Away_FIFA_Ova",\n')
        new_lines.append('    "Home_Market_Value", "Away_Market_Value",\n')
        new_lines.append('    "Home_Att_Strength", "Away_Att_Strength",\n')
        new_lines.append('    "Home_Def_Weakness", "Away_Def_Weakness",\n')
        new_lines.append('    "Home_H2H_L3", "Away_H2H_L3",\n')
        new_lines.append('    "Home_Rest_Days", "Away_Rest_Days"\n')
        new_lines.append(']\n')
        new_lines.append('# Filter to only features that exist in df\n')
        new_lines.append('features = [f for f in features if f in df.columns]\n')
        continue
    
    if skip_until_bracket:
        # Skip lines until we pass the closing bracket and filter line
        if 'features = [f for f in features' in line:
            skip_until_bracket = False
        elif line.strip() == ']':
            skip_until_bracket = False
        continue
    
    # Also skip individual feature lines from previous injection
    stripped = line.strip()
    if stripped.startswith('"Home_') or stripped.startswith('"Away_'):
        if stripped.endswith(',') or stripped.endswith('"'):
            continue
    
    new_lines.append(line)

cell['source'] = new_lines
nb['cells'][4] = cell

# Also fix Season NaN in Cell 3 (add season fix after loading)
cell3 = nb['cells'][3]
src3 = ''.join(cell3.get('source', []))
if 'Season fix' not in src3:
    # Add season NaN fix at the end of cell 3
    cell3['source'].append('\n')
    cell3['source'].append('# Season fix: fill NaN seasons based on date\n')
    cell3['source'].append('if df["Season"].isna().any():\n')
    cell3['source'].append('    df["Date"] = pd.to_datetime(df["Date"])\n')
    cell3['source'].append('    mask = df["Season"].isna()\n')
    cell3['source'].append('    df.loc[mask, "Season"] = df.loc[mask, "Date"].apply(lambda d: d.year if d.month >= 8 else d.year - 1)\n')
    cell3['source'].append('    df["Season"] = df["Season"].astype(int)\n')
    cell3['source'].append('    print(f"Fixed {mask.sum()} rows with NaN Season")\n')

with open(path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print('OK - notebook fixed:')
print('  1. Features updated to match df_final_app.csv column names')
print('  2. Season NaN fix added to cell 3')
