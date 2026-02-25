import json
import os
import re

target_dir = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\Premier\notebooks"

nb02 = os.path.join(target_dir, "02_Modelado_Avanzado_Academic_v2.ipynb")
with open(nb02, 'r', encoding='utf-8') as f:
    data = json.load(f)

pl_map = """team_map = {
    'Man United': 'Manchester United',
    'Man City': 'Manchester City',
    'Spurs': 'Tottenham Hotspur',
    'Newcastle': 'Newcastle United',
    'Leicester': 'Leicester City',
    'Norwich': 'Norwich City',
    'Leeds': 'Leeds United',
    'Sheffield United': 'Sheffield Utd',
    'West Ham': 'West Ham United',
    'Wolves': 'Wolverhampton Wanderers',
    'Brighton': 'Brighton & Hove Albion',
    'Cardiff': 'Cardiff City',
    'Swansea': 'Swansea City',
    'Stoke': 'Stoke City',
    'Hull': 'Hull City',
    'QPR': 'Queens Park Rangers',
    'West Brom': 'West Bromwich Albion',
    'Bournemouth': 'AFC Bournemouth',
    "Nott'm Forest": 'Nottingham Forest',
    'Luton': 'Luton Town',
    'Ipswich': 'Ipswich Town'
}"""

for cell in data.get('cells', []):
    if 'source' in cell:
        inside_map = False
        new_source = []
        for line in cell['source']:
            if line.startswith('team_map = {'):
                inside_map = True
                new_source.append(pl_map + '\n')
            elif inside_map:
                if '}' in line and not line.strip().startswith("'"):
                    inside_map = False
            else:
                new_source.append(line)
        cell['source'] = new_source

with open(nb02, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=1, ensure_ascii=False)

print("Updated 02 Notebook mapping.")
