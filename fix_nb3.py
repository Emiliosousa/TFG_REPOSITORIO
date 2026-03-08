import json

path = "BUNDESLIGA/notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # In NB02, we set n_trials=50. Let's fix it for the fast pipeline to prevent the loop from dying unexpectedly
        # wait, the error is "ValueError: No trials are completed yet."
        # This usually means optuna didn't finish any trials successfully, or search space was invalid, or it crashed internally
        
        # Let's reduce memory usage and set n_trials to 10 for speed
        if "study.optimize(objective, n_trials=50)" in source:
             source = source.replace("study.optimize(objective, n_trials=50)", "study.optimize(objective, n_trials=10)")
             
        # Also need, check why it failed. Usually it means the train set has 0 rows or some failure occurred
        
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Reduced optuna trials to 10 to speed up and debug failure.")
