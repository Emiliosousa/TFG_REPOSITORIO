import json

path = "notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # 1. Update dropna to use Max odds
        source = source.replace("['Target', 'B365H', 'B365D', 'B365A']", "['Target', 'MaxH', 'MaxD', 'MaxA']")
        
        # 2. Update implied_probs_train
        source = source.replace("['B365A', 'B365D', 'B365H']", "['MaxA', 'MaxD', 'MaxH']")
        
        # 3. Add date_series for Optuna
        if "season_series = df.loc[train_mask, 'Season'].reset_index(drop=True)" in source and "date_series" not in source:
            target = "season_series = df.loc[train_mask, 'Season'].reset_index(drop=True)"
            replacement = "season_series = df.loc[train_mask, 'Season'].reset_index(drop=True)\ndate_series = df.loc[train_mask, 'Date'].reset_index(drop=True)"
            source = source.replace(target, replacement)
            
        # 4. Inject sample weights in Optuna loop
        optuna_fit_target = "model.fit(X_opt[tr_mask], y_opt[tr_mask])"
        if optuna_fit_target in source and "sample_weight" not in source:
            opt_replacement = """        tr_dates = date_series[tr_mask]
        max_date = tr_dates.max()
        decay_param = 0.002 # halflife of ~ 1 year (0.693 / 365)
        weights = np.exp((tr_dates - max_date).dt.days * decay_param)
        model.fit(X_opt[tr_mask], y_opt[tr_mask], sample_weight=weights)"""
            source = source.replace(optuna_fit_target, opt_replacement)
            
        # 5. Inject sample weights in Backtest loop
        backtest_fit_target = "fold_model.fit(X_tr, y_tr)"
        if backtest_fit_target in source and "sample_weight" not in source:
            bt_replacement = """    tr_dates = df_bt.loc[tr_mask, 'Date']
    max_date = tr_dates.max()
    decay_param = 0.002
    weights = np.exp((tr_dates - max_date).dt.days * decay_param)
    fold_model.fit(X_tr, y_tr, sample_weight=weights)"""
            source = source.replace(backtest_fit_target, bt_replacement)
            
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Injected Max Odds and Exponential Decay Sample Weights.")
