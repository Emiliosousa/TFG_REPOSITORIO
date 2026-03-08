import json

path = "notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # 6. Align odds cols to Max in Backtest
        source = source.replace("ODDS_COLS_ALIGNED = ['B365A', 'B365D', 'B365H']", "ODDS_COLS_ALIGNED = ['MaxA', 'MaxD', 'MaxH']")
        
        # 7. Make sure dropna in Backtest utilizes Max odds
        source = source.replace("df_bt = df_bt.dropna(subset=ODDS_COLS_ALIGNED + FEATURES + ['Target'])", "df_bt = df_bt.dropna(subset=ODDS_COLS_ALIGNED + FEATURES + ['Target'])")

        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Injected Max Odds in Backtest.")
