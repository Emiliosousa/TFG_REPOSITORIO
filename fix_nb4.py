import json
import os

path = "BUNDESLIGA/notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # NaN in Brier score calculation usually means preds are Nan (maybe empty validation fold) 
        # Or missing probability mapping. Let's add a safe fallback to Brier calculation.
        
        if "brier = np.mean(np.sum((probs - (np.eye(3)[y_opt[val_mask]]))**2, axis=1))" in source:
             source = source.replace("brier = np.mean(np.sum((probs - (np.eye(3)[y_opt[val_mask]]))**2, axis=1))",
"""# Optimizamos basándonos en Calibración (Brier Score)
        if len(probs) == 0:
            brier = 1.0 # Penalize empty folds
        else:
            brier = np.mean(np.sum((probs - (np.eye(3)[y_opt[val_mask]]))**2, axis=1))
        
        if np.isnan(brier):
            brier = 1.0 # Penalize NaN
""")
             
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Optuna NaN bug patched.")
