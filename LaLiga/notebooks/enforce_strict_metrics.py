import json
import os

path = "02_Modelado_Avanzado_v3.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # 3. FILTRO ESTRICTO EV > 1.05 (Ventaja mínima 5%) y Kelly Fraccional 1/8
        if "MIN_EV           = 0.03" in source:
            source = source.replace("MIN_EV           = 0.03", 
"""# ============================================================================
# 🛡️ FILTRO DE VALOR ESTRICTO (Mínimo 5% EV)
# Evitamos apostar todo si la ventaja roza el cero (sobreconfianza estadística).
# Solo permitimos apuestas si el mercado nos regala un 5% de EV puro (+1.05 ROI)
# ============================================================================
MIN_EV           = 0.05   # Requisito de EV subido del 3% al 5% para proteger bankroll""")
            
        if "KELLY_FRACTION   = 0.25" in source:
             source = source.replace("KELLY_FRACTION   = 0.25   # Kelly conservador (1/4)", "KELLY_FRACTION   = 0.125  # Kelly ultra conservador (1/8 de la fracción pura para evadir Drawdown máximo)")
             
        # 4. VALIDACIÓN WALK-FORWARD CON VENTANA EXPANSIVA
        # We need to find the train assignment
        if "train_seasons = seasons_bt[i : i + WINDOW_SIZE]" in source:
             source = source.replace("train_seasons = seasons_bt[i : i + WINDOW_SIZE]", 
"""# 📅 VALIDACIÓN WALK-FORWARD (VENTANA EXPANSIVA)
    # Entrenamos con T1 a T5, predecimos T6. Luego T1 a T6, predecimos T7. 
    # Mantiene TODO el histórico sin descartarlo, asimilando Concept Drift.
    train_seasons = seasons_bt[: i + WINDOW_SIZE]""")

        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook 02_Modelado_Avanzado_v3.ipynb actualizado con Fracción Kelly a 0.125 (1/8), EV estricto > 5% y Ventana Expansiva de Backtest.")
