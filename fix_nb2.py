import json
import os

path = "BUNDESLIGA/notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # fix paths to search correctly for the file we just generated
        if "'../df_final_app.csv'," in source:
             source = source.replace("'../df_final_app.csv',", 
                                     "'../df_final_app.csv',\n    '../data/processed/df_final_app.csv',\n    '../data/processed/df_final_clean.csv',")
             
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Paths in NB 02 fixed.")
