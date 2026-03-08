import json

path = "BUNDESLIGA/notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'markdown':
        source = "".join(cell['source'])
        source = source.replace("LaLiga Prediction Model", "Bundesliga Prediction Model")
        source = source.replace("LaLiga", "Bundesliga")
        cell['source'] = source.splitlines(True)
        
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        source = source.replace("'LaLiga Prediction Model", "'Bundesliga Prediction Model")
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook 02 moved and renamed to Bundesliga successfully.")
