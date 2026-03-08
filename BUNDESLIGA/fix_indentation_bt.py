import json

path = "notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        target = '''    fold_model = CalibratedClassifierCV(fold_base, method='isotonic', cv=3)
        tr_dates = df_bt.loc[tr_mask, 'Date']
    max_date = tr_dates.max()
    decay_param = 0.002
    weights = np.exp((tr_dates - max_date).dt.days * decay_param)
    fold_model.fit(X_tr, y_tr, sample_weight=weights)'''
        
        rep = '''    fold_model = CalibratedClassifierCV(fold_base, method='isotonic', cv=3)
    tr_dates = df_bt.loc[tr_mask, 'Date']
    max_date = tr_dates.max()
    decay_param = 0.002
    weights = np.exp((tr_dates - max_date).dt.days * decay_param)
    fold_model.fit(X_tr, y_tr, sample_weight=weights)'''
        
        # In case the exact string wasn't found due to preceding characters, let's do safe string replace
        if "        tr_dates = df_bt.loc[tr_mask, 'Date']" in source:
             source = source.replace("        tr_dates = df_bt.loc[tr_mask, 'Date']", "    tr_dates = df_bt.loc[tr_mask, 'Date']")
             
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Indentation fixed.")
