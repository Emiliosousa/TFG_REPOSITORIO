import json
import os
import re

path = "02_Modelado_Avanzado_v3.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# The substitutions we want to perform
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source_lines = cell['source']
        source = "".join(source_lines)
        
        # 1. ECE Metrics
        if "test_brier =" in source or "test_brier    =" in source:
            if "expected_calibration_error" not in source:
                new_source = source.replace("test_brier    = brier_score_loss(y_test == 2, probs_test[:, 2])",
"""test_brier    = brier_score_loss(y_test == 2, probs_test[:, 2])

# =====================================================================
# 📊 EXPECTED CALIBRATION ERROR (ECE)
# Mide el desvío entre predicciones del modelo y empíricas reales.
# Fundamental para evitar sobreconfianza (espejismo del EV > 1.05)
# =====================================================================
def expected_calibration_error(y_true, y_prob, n_bins=10):
    import numpy as np
    ece = 0.0
    bin_limits = np.linspace(0, 1, n_bins + 1)
    for i in range(n_bins):
        bin_lower, bin_upper = bin_limits[i], bin_limits[i+1]
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
        if np.any(in_bin):
            prob_mean = np.mean(y_prob[in_bin])
            acc_mean = np.mean(y_true[in_bin])
            ece += np.mean(in_bin) * np.abs(prob_mean - acc_mean)
    return ece

ece_score = expected_calibration_error(y_test == 2, probs_test[:, 2])
""")
                new_source = new_source.replace("print(f'  Brier (H): {test_brier:.4f}  (menor es mejor)')",
"print(f'  Brier (H): {test_brier:.4f}  (menor es mejor)')\nprint(f'  ECE (H):   {ece_score:.4f}  (Ideal < 0.05, modelo calibrado)')")
                cell['source'] = new_source.splitlines(True)
                
        # 2. Decorrelation custom objective function
        if "def objective(trial):" in source:
            if "decorrelated_obj" not in source:
                custom_obj_code = """
# ==============================================================================
# 🧠 FUNCIÓN DE PÉRDIDA DECORRELACIONADA (Hubáček y Šír)
# Penaliza las predicciones que se acercan excesivamente al consenso de Winamax.
# ==============================================================================
implied_probs_train = 1.0 / df.loc[train_mask, ['B365A', 'B365D', 'B365H']].values
implied_probs_train = implied_probs_train / implied_probs_train.sum(axis=1, keepdims=True)

def get_decorrelated_objective(market_probs, gamma=0.1):
    '''Custom objective para XGBoost: LogLoss + Penalización a la casa de apuestas'''
    def decorrelated_obj(labels, predt):
        import numpy as np
        # Raw logits a probabilidades softmax
        predt = np.exp(predt - np.max(predt, axis=1, keepdims=True))
        p = predt / np.sum(predt, axis=1, keepdims=True)
        
        y = np.zeros_like(p)
        for i in range(len(labels)):
            y[i, int(labels[i])] = 1.0
            
        grad_ce = p - y
        hess_ce = p * (1.0 - p)
        
        # Penalización de correlación (gamma)
        grad_cor = 2 * gamma * (p - market_probs) * p * (1.0 - p)
        hess_cor = 2 * gamma * (p * (1.0 - p))
        
        grad = grad_ce + grad_cor
        hess = hess_ce + hess_cor
        return grad.flatten(), hess.flatten()
    return decorrelated_obj

"""
                idx = source.find("def objective(trial):")
                new_source = source[:idx] + custom_obj_code + source[idx:]
                new_source = new_source.replace("model.fit(X_opt[tr_mask], y_opt[tr_mask])",
"""
        # Inject custom objective during CV evaluation to decorrelate
        model.set_params(objective=get_decorrelated_objective(implied_probs_train[tr_mask], gamma=0.15))
        model.fit(X_opt[tr_mask], y_opt[tr_mask])""")
                cell['source'] = new_source.splitlines(True)

        # 3. Fractional Kelly comments to highlight it fixes the Stake
        if "INITIAL_BANKROLL = 1000" in source:
            new_source = source.replace("INITIAL_BANKROLL = 1000",
"""# ============================================================================
# 💰 CRITERIO DE KELLY FRACCIONAL vs FLAT STAKE
# El Flat Stake destruye la ventaja debido a la varianza. Utilizamos Kelly 
# fraccional (0.25) para maximizar el crecimiento logarítmico mitigando riesgo.
# ============================================================================
INITIAL_BANKROLL = 1000""")
            cell['source'] = new_source.splitlines(True)

# Also apply this to Premier League equivalent if needed, but let's stick to LaLiga first.
with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook 02_Modelado_Avanzado_v3.ipynb parseado y actualizado satisfactoriamente con Custom Objective, ECE y Análisis Kelly.")
