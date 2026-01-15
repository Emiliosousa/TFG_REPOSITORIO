import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import re
from sklearn.model_selection import StratifiedKFold, cross_val_score
import optuna
import os

# Config
TEST_SEASON = 2023
TARGET = 'FTR_Num'
MODEL_FILE = 'modelo_city_group.joblib'
DATA_FILE = 'df_final_app.csv'

print("🚀 Starting Model Retraining (Source: APP DB)...")

# 1. Load Data
if not os.path.exists(DATA_FILE):
    print(f"❌ Error: {DATA_FILE} not found.")
    exit(1)

df = pd.read_csv(DATA_FILE)
# Cleanup duplicates (if merge created suffixes)
df = df.loc[:, ~df.columns.str.endswith('.1')]
print(f"📚 Data Loaded: {len(df)} rows")

# 2. Preprocessing & Debugging
# Cleanup duplicates (regex to remove .1, .2, etc)
# Strategy: Keep the first occurrence of base name?
# Or just drop columns that match pattern \.\d+$
df = df.loc[:, ~df.columns.str.contains(r'\.\d+$', regex=True)]

print("📊 Data Inspection:")
print(df['Season'].value_counts().sort_index())

# Fill NaNs instead of dropping all
# Rolling features might produce NaNs at the start.
df = df.fillna(0)

print(f"📚 Data After Cleanup: {len(df)} rows")

# Mapping
mapping = {'A': 0, 'D': 1, 'H': 2}
if 'FTR' in df.columns:
    df['FTR_Num'] = df['FTR'].map(mapping)
else:
    print("❌ Error: 'FTR' column missing.")
    exit(1)

# Split
# Check if TEST_SEASON exists
if TEST_SEASON not in df['Season'].unique():
    print(f"⚠️ TEST_SEASON {TEST_SEASON} not found! Switching to max season - 1.")
    TEST_SEASON = df['Season'].max() - 1

train_mask = df['Season'] < TEST_SEASON
test_mask = df['Season'] == TEST_SEASON

df_train = df[train_mask].copy()
df_test = df[test_mask].copy()

print(f"📉 Train Set: {len(df_train)} rows (Season < {TEST_SEASON})")
print(f"📈 Test Set:  {len(df_test)} rows (Season = {TEST_SEASON})")

if len(df_train) == 0 or len(df_test) == 0:
    print("❌ Error: Train or Test set is empty. Aborting.")
    exit(1)

# 3. Define Features (The NEW Full List)
features = [
    'Home_Elo', 'Away_Elo',
    'Home_Att_Strength', 'Away_Att_Strength',
    'Home_Def_Weakness', 'Away_Def_Weakness',
    'Home_FIFA_Ova', 'Away_FIFA_Ova',
    'Home_Market_Value', 'Away_Market_Value',
    'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
    'Home_Streak_L5', 'Away_Streak_L5',
    'Home_H2H_L3', 'Away_H2H_L3',
    'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
    'Home_Goal_Diff_L5', 'Away_Goal_Diff_L5',
    'Home_Rest_Days', 'Away_Rest_Days'
]

# Validation
valid_features = [f for f in features if f in df_train.columns]
print(f"✅ Features found: {len(valid_features)} / {len(features)}")
if len(valid_features) != len(features):
    missing = set(features) - set(valid_features)
    print(f"❌ CRITICAL ERROR: Missing features in CSV: {missing}")
    # Force error to prevent bad model
    exit(1)

X_train = df_train[valid_features]
y_train = df_train['FTR_Num']
X_test = df_test[valid_features]
y_test = df_test['FTR_Num']

# 3. Simple Training (Skip Optuna for speed, use decent defaults or just quick optimize)
# We will use the params from the previous best run found in the notebook if possible, 
# or just run a quick optuna. Let's run a quick optuna (5 trials) to be safe.

def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 300),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
        'max_depth': trial.suggest_int('max_depth', 3, 6),
        'subsample': trial.suggest_float('subsample', 0.7, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 1.0),
        'objective': 'multi:softprob',
        'num_class': 3,
        'n_jobs': -1,
        'random_state': 42,
        'verbosity': 0
    }
    
    model = xgb.XGBClassifier(**params)
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='neg_log_loss')
    return scores.mean()

print("🔍 Optimizing Hyperparameters (Quick)...")
optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=5)

best_params = study.best_params
best_params.update({'objective': 'multi:softprob', 'num_class': 3, 'n_jobs': -1, 'random_state': 42})
print(f"🏆 Best Params: {best_params}")

# Train Final
print("🏋️ Training Final Model...")
final_model = xgb.XGBClassifier(**best_params)
final_model.fit(X_train, y_train)

# Save
artifact = {
    'model': final_model,
    'features': valid_features,
    'version': '2.1_Unified'
}
joblib.dump(artifact, MODEL_FILE)
print(f"💾 Model Retrained and Saved to {MODEL_FILE}")
