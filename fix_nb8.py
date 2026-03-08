import json

path = "BUNDESLIGA/notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        target1 = "CSV_PATH = '../data/processed/df_final_clean.csv'"
        rep1 = "import os\nCSV_PATH = os.path.join(os.path.dirname('__file__'), '../data/processed/df_final_clean.csv')"
        
        if target1 in source:
             source = source.replace(target1, rep1)
             
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Path fixed internally inside notebook JSON.")
