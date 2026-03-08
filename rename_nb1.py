import json

path = "BUNDESLIGA/notebooks/01_Ingenieria_de_Datos_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'markdown':
        source = "".join(cell['source'])
        source = source.replace("LaLiga", "Bundesliga")
        cell['source'] = source.splitlines(True)
        
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        source = source.replace("LaLiga", "BUNDESLIGA")
        source = source.replace("df_laliga", "df_bundesliga")
        source = source.replace("LaLiga EA Sports", "Bundesliga")
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook 01 renamed and ready.")
