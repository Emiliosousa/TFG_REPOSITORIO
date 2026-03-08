import json

path = "BUNDESLIGA/notebooks/01_Ingenieria_de_Datos_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # Replace display functions with print for safe execution outside purely jupyter
        if "display(" in source:
             source = source.replace("display(", "print(")
             
        # Redirect data paths from laliga defaults to current bundesliga structure
        if "df_laliga_consolidated.csv" in source:
             source = source.replace("df_laliga_consolidated.csv", "processed/df_final_clean.csv")
        
        if "../data/" in source and "processed/" not in source:
             source = source.replace("../data/", "../data/processed/")
             
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook 01 display and path references fixed.")
