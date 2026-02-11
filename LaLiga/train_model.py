



































import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import json
import sys
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, log_loss

import os

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# ROOT_DIR = os.path.dirname(SCRIPT_DIR) # Not needed if files are in LaLiga folder

DATA_FILE = os.path.join(SCRIPT_DIR, 'df_final_app.csv')
MODEL_FILE = os.path.join(SCRIPT_DIR, 'modelo_city_group.joblib')
METRICS_FILE = os.path.join(SCRIPT_DIR, 'validation_metrics.json')

MODEL_FEATURES = [
    'Home_Elo', 'Away_Elo', 'Home_Att_Strength', 'Away_Att_Strength',
    'Home_Def_Weakness', 'Away_Def_Weakness', 'Home_FIFA_Ova', 'Away_FIFA_Ova',
    'Home_Market_Value', 'Away_Market_Value', 'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
    'Home_Streak_L5', 'Away_Streak_L5', 'Home_H2H_L3', 'Away_H2H_L3',
    'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5', 'Home_Goal_Diff_L5', 'Away_Goal_Diff_L5',
    'Home_Rest_Days', 'Away_Rest_Days', 'Home_Dominance_Avg_L5', 'Away_Dominance_Avg_L5'
]

XGB_PARAMS = {
    'objective': 'multi:softprob',
    'num_class': 3,
    'max_depth': 4,
    'learning_rate': 0.05,
    'n_estimators': 150,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'eval_metric': 'mlogloss',
    'random_state': 42
}

def main():
    print("LOADING DATA...")
    try:
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)
    except FileNotFoundError:
        print(f"Error: {DATA_FILE} not found.")
        sys.exit(1)

    # Clean & Prepare
    # Map FTR: A=0, D=1, H=2 (Standard XGBoost mapping)
    mapping = {'A': 0, 'D': 1, 'H': 2}
    df = df[df['FTR'].isin(mapping.keys())].copy()
    df['FTR_Num'] = df['FTR'].map(mapping)
    
    # Check Features
    missing = [f for f in MODEL_FEATURES if f not in df.columns]
    if missing:
        print(f"Error: Missing features: {missing}")
        sys.exit(1)
        
    X = df[MODEL_FEATURES]
    y = df['FTR_Num']
    
    print(f"\nMODEL TRAINING - TIME SERIES SPLIT (5 Folds)")
    print("="*50)
    
    tscv = TimeSeriesSplit(n_splits=5)
    results = []
    
    fold = 1
    for train_index, test_index in tscv.split(X):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        
        model = xgb.XGBClassifier(**XGB_PARAMS)
        model.fit(X_train, y_train)
        
        preds = model.predict(X_test)
        
        # Metrics (Weighted for multi-class)
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, average='weighted', zero_division=0)
        rec = recall_score(y_test, preds, average='weighted', zero_division=0)
        f1 = f1_score(y_test, preds, average='weighted', zero_division=0)
        
        print(f"Fold {fold}: Train {len(X_train)} | Test {len(X_test)} | Acc {acc:.4f} | Prec {prec:.4f} | F1 {f1:.4f}")
        
        results.append({
            "fold": fold,
            "train_size": len(X_train),
            "test_size": len(X_test),
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4)
        })
        fold += 1
        
    # Aggregate Metrics
    avg_acc = np.mean([r['accuracy'] for r in results])
    std_acc = np.std([r['accuracy'] for r in results])
    avg_f1 = np.mean([r['f1'] for r in results])
    
    print("\nCROSS-VALIDATION RESULTS")
    print("="*50)
    print(f"Mean Accuracy:  {avg_acc:.4f} (+/- {std_acc:.4f})")
    print(f"Mean F1-Score:  {avg_f1:.4f}")
    
    # Save Metrics for Dashboard
    with open(METRICS_FILE, 'w') as f:
        json.dump(results, f, indent=4)
        
    print("\nFINAL MODEL TRAINING ON FULL DATASET")
    print("="*50)
    final_model = xgb.XGBClassifier(**XGB_PARAMS)
    final_model.fit(X, y)
    
    # Save Artifact
    artifact = {
        'model': final_model,
        'features': MODEL_FEATURES,
        'cv_results': results,
        'training_date': str(pd.Timestamp.now())
    }
    joblib.dump(artifact, MODEL_FILE)
    print(f"Model saved to: {MODEL_FILE}")
    print("TRAINING COMPLETE")

if __name__ == "__main__":
    main()
