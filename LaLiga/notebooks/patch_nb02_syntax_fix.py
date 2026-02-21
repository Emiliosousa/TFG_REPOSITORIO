import nbformat
import os

NOTEBOOK_PATH = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\notebooks\02_Modelado_Avanzado_Academic_v2.ipynb"

# --- CLEAN AND CORRECTED OBJECTIVE FUNCTION ---
# Features:
# 1. Correct Indentation (Fixes SyntaxError)
# 2. Multi-class 'multi:softprob' from start (Fixes 1X2 issue)
# 3. Global variable access (X, y, season_series, df_final)
# 4. Vectorized Betting Simulation (Max EV strategy)

NEW_OBJECTIVE_CODE = r"""
def objective(trial):
    import numpy as np
    import xgboost as xgb
    
    # 1. Hyperparameters
    param = {
        'objective': 'multi:softprob',
        'num_class': 3,
        'eval_metric': 'mlogloss', 
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.08),  # CAP at 0.08
        'max_depth': trial.suggest_int('max_depth', 2, 4),  # CAP at 4
        'n_estimators': 500,  # FIXED
        'subsample': trial.suggest_float('subsample', 0.6, 0.9),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 0.9),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
        'random_state': 42,
        'n_jobs': -1,
        'verbosity': 0
    }
    
    # 2. Walk-Forward Validation
    rois = []
    
    # Ensure seasons are sorted
    unique_seasons = sorted(season_series.unique())
    
    # Start validation from 6th season (need history)
    for i in range(5, len(unique_seasons)):
        train_seasons = unique_seasons[:i]
        val_season = unique_seasons[i]
        
        train_mask = season_series.isin(train_seasons)
        val_mask = season_series == val_season
        
        X_train, y_train = X[train_mask], y[train_mask]
        X_val, y_val = X[val_mask], y[val_mask]
        
        # Train
        model = xgb.XGBClassifier(**param)
        model.fit(X_train, y_train)
        
        # Predict Probabilities (Shape: N x 3 for A, D, H)
        probs_matrix = model.predict_proba(X_val)
        
        # 3. Betting Simulation
        val_indices = X_val.index
        # Get Odds: Indices 0, 1, 2 must match Target 0(A), 1(D), 2(H)
        # Verify columns exist. If not found, skip or zero.
        try:
            val_odds = df_final.loc[val_indices, ['B365A', 'B365D', 'B365H']].values
        except KeyError:
            # Fallback if specific odds columns missing (should check cols first)
            # Assuming standard naming
            continue
            
        # EV Calculation: EV = (Prob * Odds) - 1
        ev_matrix = (probs_matrix * val_odds) - 1
        
        # Find Best Bet per match
        best_bet_idx = np.argmax(ev_matrix, axis=1) # 0, 1, or 2
        best_ev = np.max(ev_matrix, axis=1)
        
        # Filter: EV > 3%
        bet_mask = best_ev > 0.03
        
        # If no bets in this seeason, ROI is 0% (neutral)
        if bet_mask.sum() == 0:
            rois.append(0.0)
            continue
            
        # Kelly Criterion
        # b = Odds - 1
        # p = Prob
        # f = (bp - q) / b
        
        selected_odds = val_odds[np.arange(len(val_odds)), best_bet_idx]
        selected_probs = probs_matrix[np.arange(len(probs_matrix)), best_bet_idx]
        
        # Filter arrays by mask
        b = selected_odds[bet_mask] - 1
        p = selected_probs[bet_mask]
        
        if len(b) == 0: 
            rois.append(0.0)
            continue

        f = (b * p - (1 - p)) / b
        
        # Fractional Kelly (25%) & Cap (5%)
        f = f * 0.25
        f = np.clip(f, 0.0, 0.05)
        
        # Calculate Profit
        # Did we win?
        actual_outcomes = y_val.values[bet_mask]
        bet_predictions = best_bet_idx[bet_mask]
        
        wins = (actual_outcomes == bet_predictions)
        
        profit = np.zeros_like(f)
        profit[wins] = f[wins] * b[wins]
        profit[~wins] = -f[~wins]
        
        # Season ROI
        total_staked = f.sum()
        total_profit = profit.sum()
        
        if total_staked <= 0.0001:
            season_roi = 0.0
        else:
            season_roi = total_profit / total_staked
            
        rois.append(season_roi)
        
    # Return Mean ROI across valid seasons
    if len(rois) == 0:
        return 0.0
    return np.mean(rois)
"""

def fix_notebook():
    if not os.path.exists(NOTEBOOK_PATH):
        print(f"Notebook not found: {NOTEBOOK_PATH}")
        return

    nb = nbformat.read(NOTEBOOK_PATH, as_version=4)
    
    # Find the cell defining "def objective(trial):"
    target_idx = -1
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == 'code' and "def objective(trial):" in cell.source:
            target_idx = i
            break
            
    if target_idx != -1:
        print(f"Found objective function at cell {target_idx}. Replacing...")
        nb.cells[target_idx] = nbformat.v4.new_code_cell(NEW_OBJECTIVE_CODE)
        nbformat.write(nb, NOTEBOOK_PATH)
        print("✅ Notebook patched: Syntax error fixed & Logic consolidated.")
    else:
        print("❌ Could not find 'def objective(trial)' cell to fix.")

if __name__ == "__main__":
    fix_notebook()
