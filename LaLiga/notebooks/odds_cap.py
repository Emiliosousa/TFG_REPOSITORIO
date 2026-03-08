import json

path = "02_Modelado_Avanzado_v3.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # A) IMPLEMENTAR ODDS CAP
        if "p    = row[prob_col]" in source and "odds = row[odds_col]" in source:
            if "if odds > 4.50:" not in source:
                 source = source.replace("ev   = p * odds - 1",
"""ev   = p * odds - 1

            # A) LÍMITE DE CUOTA (ODDS CAP)
            # Descartamos underdogs extremos (> 4.50) donde la casa esconde su margen mayor
            if odds > 4.50:
                continue""")
                 
        # B) ACTUALIZAR MIN_EV Y KELLY
        if "MIN_EV           = 0.04" in source:
            source = source.replace("MIN_EV           = 0.04", "MIN_EV           = 0.06")
            
        if "KELLY_FRACTION   = 0.10" in source:
            source = source.replace("KELLY_FRACTION   = 0.10", "KELLY_FRACTION   = 0.05")

        # C) DEVOLVER LA CALIBRACIÓN A ISOTÓNICA
        if "method='sigmoid'" in source:
             source = source.replace("method='sigmoid'", "method='isotonic'")
        if "Calibración Platt Scaling (Sigmoid)" in source:
             source = source.replace("Calibración Platt Scaling (Sigmoid)", "Calibración Isotónica")
             
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("✅ Odds Cap < 4.50, Calibración Isotónica, EV > 1.06 y Kelly 1/20 aplicados con éxito.")
