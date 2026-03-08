import json

path = "BUNDESLIGA/notebooks/02_Modelado_Avanzado_v3_Bundesliga.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # We need to drop NA values for odds and features right before using them for Optuna
        # Currently, X and y are defined as:
        # X      = df[FEATURES].astype(float)
        # y      = df['Target'].astype(int)
        
        # Let's intercept right after FEATURES declaration and before X / y creation
        if "X      = df[FEATURES].astype(float)" in source:
             source = source.replace("X      = df[FEATURES].astype(float)",
"""# Drop NA values across Features and Odds globally before any train/optuna logic
df = df.dropna(subset=FEATURES + ['Target', 'B365H', 'B365D', 'B365A']).reset_index(drop=True)

# Actualizar mascaras temporales tras dropna
train_mask = df['Season'] < TEST_SEASON_START
test_mask  = df['Season'] >= TEST_SEASON_START

X      = df[FEATURES].astype(float)""")
             
        cell['source'] = source.splitlines(True)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Added global dropna for features and odds to prevent NaN in Optuna custom objective.")
