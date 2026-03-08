import json
import re

path = "notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # Remove custom objective injection
        patch = re.sub(r'model\.set_params\(objective=get_decorrelated_objective.*?\)\n', '', source)
        
        cell['source'] = patch.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Custom objective removed to allow sample_weight usage.")
