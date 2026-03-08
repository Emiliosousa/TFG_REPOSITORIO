import json
import os

path = "LaLiga/notebooks/02_Modelado_Avanzado_v3.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # Sec 7: plot
        source = source.replace("flat_roi_g", "flat_yield_g")
        source = source.replace("kelly_roi_g", "kelly_yield_g")
        source = source.replace("df_seasons['Flat_ROI']", "df_seasons['Yield_Flat']")
        
        # Sec 8: table
        source = source.replace("'Flat_ROI'", "'Yield_Flat'")
        source = source.replace("'Kelly_ROI'", "'Yield_Kelly'")
        
        # Update cell lines
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Vars fixed in LaLiga")
