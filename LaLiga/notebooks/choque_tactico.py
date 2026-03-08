import json

path = "02_Modelado_Avanzado_v3.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # A) Cambiar Regresión Isotónica a Platt Scaling (sigmoid)
        if "method='isotonic'" in source:
            source = source.replace("method='isotonic'", "method='sigmoid'")
            source = source.replace("Calibración isotónica", "Calibración Platt Scaling (Sigmoid)")

        # B) Apagar temporalmente la Penalización de Hubáček (Gamma = 0)
        if "def get_decorrelated_objective(market_probs, gamma=0.2):" in source:
            source = source.replace("def get_decorrelated_objective(market_probs, gamma=0.2):", 
                                    "def get_decorrelated_objective(market_probs, gamma=0.0):")
            
        if "gamma=0.15" in source:
            source = source.replace("gamma=0.15", "gamma=0.0")

        # C) Bajar el filtro de EV a 1.04 y el Kelly a 1/10
        if "MIN_EV           = 0.10" in source:
            source = source.replace("MIN_EV           = 0.10", "MIN_EV           = 0.04")
            
        if "KELLY_FRACTION   = 0.125" in source:
            source = source.replace("KELLY_FRACTION   = 0.125  # Kelly ultra conservador (1/8 de la fracción pura para evadir Drawdown máximo)",
                                    "KELLY_FRACTION   = 0.10   # Décimo de Kelly (1/10) - Volumen alto, stake muy controlado")
        elif "KELLY_FRACTION   = 0.125" in source:
            source = source.replace("KELLY_FRACTION   = 0.125", "KELLY_FRACTION   = 0.10")

        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("✅ Plan de Choque táctico aplicado: Platt Scaling, Gamma=0 y EV > 1.04 con Décimo de Kelly.")
