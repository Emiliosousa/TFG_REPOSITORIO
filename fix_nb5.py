import json

path = "BUNDESLIGA/notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # In NB02 Optuna loop, we use 'for i in range(5, len(unique_seasons))'
        # With only 5 seasons in the train_mask (2018 to 2022), 'range(5, 5)' is empty!
        # This causes the empty array NaNs we see 
        # Changing range from 5 to 3
        
        if "for i in range(5, len(unique_seasons)):" in source:
             source = source.replace("for i in range(5, len(unique_seasons)):", "for i in range(3, len(unique_seasons)):")
             
        # Also let's change WINDOW_SIZE in Backtester safely to 3 so we get more seasons in backtest
        if "WINDOW_SIZE      = 5" in source:
             source = source.replace("WINDOW_SIZE      = 5", "WINDOW_SIZE      = 3")

        # Optuna n_trials safely back to 20
        if "n_trials=10" in source:
            source = source.replace("n_trials=10", "n_trials=20")
            
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Optuna temporal loop ranges patched for smaller Bundesliga dataset size.")
