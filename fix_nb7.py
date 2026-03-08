import json

path = "BUNDESLIGA/notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # Hardcode the path strictly to BUNDESLIGA data instead of using fallback
        if "possible_paths = [" in source:
            source = """CSV_PATH = '../data/processed/df_final_clean.csv'
df = pd.read_csv(CSV_PATH)
df['Date'] = pd.to_datetime(df['Date'])
"""
            # We override the whole loading block logic for safety until Deduplicar starts
            import re
            source_cell = re.sub(r"possible_paths = \[.*?raise FileNotFoundError\('No se encontró el CSV de datos\.'\)\n\ndf = pd\.read_csv\(CSV_PATH\)\ndf\['Date'\] = pd\.to_datetime\(df\['Date'\]\)",
                                 """CSV_PATH = '../data/processed/df_final_clean.csv'
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError('No se encontró el CSV de datos de la Bundesliga en: ' + CSV_PATH)

df = pd.read_csv(CSV_PATH)
df['Date'] = pd.to_datetime(df['Date'])""", source, flags=re.DOTALL)
            
            cell['source'] = source_cell.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Path strictly fixed for BUNDESLIGA data.")
