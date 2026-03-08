import json

path = "02_Modelado_Avanzado_v3.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # 1. OPTIMIZACIÓN A BRIER SCORE (A)
        # Cambio de mlogloss a Brier en la Optuna objective function
        if "eval_metric': 'mlogloss'" in source:
             source = source.replace("eval_metric': 'mlogloss'", "eval_metric': 'mlogloss'")
             
        if "losses.append(log_loss(y_opt[val_mask], probs))" in source:
             source = source.replace("losses.append(log_loss(y_opt[val_mask], probs))",
"""# Optimizamos basándonos en Calibración (Brier Score) según Walsh y Joshi (2024)
        # Brier = (Pred - Real)^2
        brier = np.mean(np.sum((probs - (np.eye(3)[y_opt[val_mask]]))**2, axis=1))
        losses.append(brier)""")
             source = source.replace("Minimizar Log Loss = mejor calibración", "Minimizar Brier Score = mejor calibración (Walsh y Joshi)")
             source = source.replace("Mejor Log Loss validado:", "Mejor Brier Score validado:")

        # 2. SUBIR EV ESTRICTO >= 1.10 (10% Edge) (B)
        if "MIN_EV           = 0.05" in source:
             source = source.replace("MIN_EV           = 0.05",
                                     "MIN_EV           = 0.10")

        # 4. DECORRELACIÓN HUBÁČEK (C) - MSE VARIANCE PENALTY
        # Reformulando la Custom Loss de XGBoost
        if "def get_decorrelated_objective" in source:
            new_custom_loss = """def get_decorrelated_objective(market_probs, gamma=0.2):
    '''
    Custom objective de Hubáček y Šír:
    Loss = MSE(Modelo, Real) - Gamma * MSE(Modelo, CasaApuestas)
    Fuerza a cazar ineficiencias y underdogs en lugar de imitar cuotas.
    '''
    def decorrelated_obj(labels, predt):
        import numpy as np
        # Raw logits a probs
        predt = np.exp(predt - np.max(predt, axis=1, keepdims=True))
        p = predt / np.sum(predt, axis=1, keepdims=True)
        
        y = np.zeros_like(p)
        for i in range(len(labels)):
            y[i, int(labels[i])] = 1.0
            
        # Gradientes MSE base vs Real
        grad_mse = p - y
        hess_mse = np.ones_like(p)
        
        # Gradiente MSE vs Casa de Apuestas (Para penalizar similitud)
        grad_cor = -gamma * (p - market_probs)
        hess_cor = -gamma * np.ones_like(p)
        
        grad = grad_mse + np.clip(grad_cor, -0.5, 0.5)
        hess = np.clip(hess_mse + hess_cor, 1e-6, None) # Hessiano siempre positivo para XGBoost
        return grad.flatten(), hess.flatten()
    return decorrelated_obj"""
            
            import re
            source = re.sub(r'def get_decorrelated_objective.*?return decorrelated_obj', new_custom_loss, source, flags=re.DOTALL)

        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Actualizaciones finales aplicadas con éxito.")
