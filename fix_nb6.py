import json
import os

path = "BUNDESLIGA/notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # Remove the problematic custom objective injection in Optuna since gamma=0.0 anyway
        # It's causing internal XGBoost evaluation errors returning NaNs.
        if "model.set_params(objective=get_decorrelated_objective(implied_probs_train[tr_mask], gamma=0.0))" in source:
             source = source.replace("model.set_params(objective=get_decorrelated_objective(implied_probs_train[tr_mask], gamma=0.0))", "")
             
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Removed custom objective set_params instruction.")
