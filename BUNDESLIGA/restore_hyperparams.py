import json

path = "notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # 1. Ensure WINDOW_SIZE is 5 now that we have 2010-2026 data
        if "WINDOW_SIZE      = 3" in source:
             source = source.replace("WINDOW_SIZE      = 3", "WINDOW_SIZE      = 5")
             
        # 2. Ensure n_trials is 50 for better calibration
        if "n_trials=20" in source:
             source = source.replace("n_trials=20", "n_trials=50")
             
        # Fix the temporal loop back to range(5, len)
        if "for i in range(3, len(unique_seasons)):" in source:
             source = source.replace("for i in range(3, len(unique_seasons)):", "for i in range(5, len(unique_seasons)):")

        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Restored original LaLiga hyperparams (Window=5, trials=50) for Bundesliga.")
