"""
Premier League Model Training with Optuna + XGBoost
"""
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import log_loss, accuracy_score
from sklearn.model_selection import TimeSeriesSplit
import joblib
import optuna
import os

optuna.logging.set_verbosity(optuna.logging.WARNING)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, 'df_premier_features.csv')
MODEL_PATH = os.path.join(SCRIPT_DIR, 'modelo_premier.joblib')

def main():
    print("🚀 Premier League Model Training")
    print("=" * 60)

    # 1. Load Data
    df = pd.read_csv(CSV_PATH)
    df['Date'] = pd.to_datetime(df['Date'])
    target_map = {'A': 0, 'D': 1, 'H': 2}
    df['Target'] = df['FTR'].map(target_map)

    features = [
        'Home_Elo', 'Away_Elo',
        'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
        'Home_Streak_L5', 'Away_Streak_L5',
        'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
        'Home_Dominance', 'Away_Dominance'
    ]

    print(f"📊 Data: {len(df)} matches")

    # 2. Split
    TEST_SEASON = 2024
    train_mask = df['Season'] < TEST_SEASON
    test_mask = df['Season'] >= TEST_SEASON

    X_train = df.loc[train_mask, features].astype(float)
    y_train = df.loc[train_mask, 'Target'].astype(int)
    X_test = df.loc[test_mask, features].astype(float)
    y_test = df.loc[test_mask, 'Target'].astype(int)

    print(f"   Train: {len(X_train)} | Test: {len(X_test)}")

    # 3. Optuna
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'gamma': trial.suggest_float('gamma', 0, 5),
            'objective': 'multi:softprob',
            'num_class': 3,
            'random_state': 42,
            'n_jobs': -1,
            'verbosity': 0
        }

        tscv = TimeSeriesSplit(n_splits=5)
        scores = []
        for tr_idx, val_idx in tscv.split(X_train):
            X_t, X_v = X_train.iloc[tr_idx], X_train.iloc[val_idx]
            y_t, y_v = y_train.iloc[tr_idx], y_train.iloc[val_idx]
            model = xgb.XGBClassifier(**params)
            model.fit(X_t, y_t, verbose=False)
            preds = model.predict_proba(X_v)
            scores.append(log_loss(y_v, preds))
        return np.mean(scores)

    print("\n⚙️ Optuna (15 trials)...")
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=15)

    print(f"   Best LogLoss CV: {study.best_value:.4f}")
    print(f"   Best params: {study.best_params}")

    # 4. Final Model
    best = study.best_params
    best['objective'] = 'multi:softprob'
    best['num_class'] = 3
    best['random_state'] = 42
    best['verbosity'] = 0

    final_model = xgb.XGBClassifier(**best)
    final_model.fit(X_train, y_train)

    probs = final_model.predict_proba(X_test)
    preds = final_model.predict(X_test)
    loss = log_loss(y_test, probs)
    acc = accuracy_score(y_test, preds)

    print(f"\n📈 TEST RESULTS:")
    print(f"   Log Loss: {loss:.4f}")
    print(f"   Accuracy: {acc:.2%}")

    # 5. Save
    joblib.dump(final_model, MODEL_PATH)
    print(f"\n💾 Model saved: {MODEL_PATH}")
    print("✅ Training Complete!")

if __name__ == '__main__':
    main()
