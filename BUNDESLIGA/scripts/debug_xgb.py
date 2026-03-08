import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import brier_score_loss

df = pd.read_csv('../data/processed/df_final_clean.csv')
print(f"Total Rows: {len(df)}")
df['Date'] = pd.to_datetime(df['Date'])
df['Target'] = df['FTR'].map({'A': 0, 'D': 1, 'H': 2})

FEATURES = [
    'Home_Elo', 'Away_Elo',
    'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
    'Home_Streak_L5', 'Away_Streak_L5',
    'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
]
optional = ['Home_FIFA_Ova', 'Away_FIFA_Ova', 'Home_Market_Value', 'Away_Market_Value']
FEATURES += [f for f in optional if f in df.columns]

print("Dropping NaNs...")
df = df.dropna(subset=FEATURES + ['Target', 'B365H', 'B365D', 'B365A']).reset_index(drop=True)
print(f"Rows after dropna: {len(df)}")

TEST_SEASON_START = 2023
train_mask = df['Season'] < TEST_SEASON_START

X = df[FEATURES].astype(float)
y = df['Target'].astype(int)

season_series = df.loc[train_mask, 'Season'].reset_index(drop=True)
X_opt = X[train_mask].reset_index(drop=True)
y_opt = y[train_mask].reset_index(drop=True)

unique_seasons = sorted(season_series.unique())
print(f"Train seasons: {unique_seasons}")

losses = []
for i in range(5, len(unique_seasons)):
    tr_seasons = unique_seasons[:i]
    val_season = unique_seasons[i]
    tr_mask  = season_series.isin(tr_seasons)
    val_mask = season_series == val_season
    print(f"Fold {i} -> Train rows: {tr_mask.sum()}, Val rows: {val_mask.sum()}")
    
    if val_mask.sum() == 0:
        continue
        
    model = xgb.XGBClassifier(objective='multi:softprob', num_class=3, eval_metric='mlogloss', n_estimators=10)
    model.fit(X_opt[tr_mask], y_opt[tr_mask])
    probs = model.predict_proba(X_opt[val_mask])
    
    brier = np.mean(np.sum((probs - (np.eye(3)[y_opt[val_mask]]))**2, axis=1))
    print(f"Brier Fold {i}: {brier}")
    losses.append(brier)

print(f"Mean loss: {np.mean(losses)}")
