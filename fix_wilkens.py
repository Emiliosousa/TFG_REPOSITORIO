import json

path = "BUNDESLIGA/notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        target = """            # A) LÍMITE DE CUOTA (ODDS CAP)"""
        replacement = """            # APOSTAR SOLO A VICTORIAS LOCALES (Regla de Wilkens, 2026)
            result_map = {0: 'A', 1: 'D', 2: 'H'}
            if result_map[outcome_idx] != 'H': 
                continue
                
            # A) LÍMITE DE CUOTA (ODDS CAP)"""
        
        if target in source:
             source = source.replace(target, replacement)
             
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Regla de Wilkens inyectada exitosamente en el notebook.")
