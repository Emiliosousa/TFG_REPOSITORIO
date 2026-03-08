import json

path = "notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        target = "                tr_dates = date_series[tr_mask]"
        rep = "        tr_dates = date_series[tr_mask]"
        
        if target in source:
             source = source.replace(target, rep)
             
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Indentation fixed.")
