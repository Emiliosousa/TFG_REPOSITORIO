import json
import re

path = "notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # 1. Fix CSV Path to ONLY load the correct Bundesliga data
        if "possible_paths = [" in source:
            source = """import os
import pandas as pd

# Path relative to notebook directory or script
current_dir = os.getcwd()
if 'notebooks' in current_dir:
    CSV_PATH = '../data/processed/df_final_clean.csv'
else:
    CSV_PATH = 'data/processed/df_final_clean.csv'

if not os.path.exists(CSV_PATH):
    raise FileNotFoundError('No se encontró el CSV de datos: ' + CSV_PATH)

df = pd.read_csv(CSV_PATH)
df['Date'] = pd.to_datetime(df['Date'])
"""
        # 2. Add Wilkens Rule (Only Home Bets)
        # Search for:
        #             # A) LÍMITE DE CUOTA (ODDS CAP)
        #             # Descartamos underdogs extremos (> 4.50)
        # Or:
        #             if odds > 4.50:
        
        target_rule = "            # A) LÍMITE DE CUOTA (ODDS CAP)"
        if target_rule in source and "Regla de Wilkens" not in source:
            replacement = """            # APOSTAR SOLO A VICTORIAS LOCALES (Regla de Wilkens, 2026)
            result_map = {0: 'A', 1: 'D', 2: 'H'}
            if result_map[outcome_idx] != 'H': 
                continue
                
            # A) LÍMITE DE CUOTA (ODDS CAP)"""
            source = source.replace(target_rule, replacement)
            
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook fixes applied successfully.")
