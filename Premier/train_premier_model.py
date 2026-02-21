import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import log_loss, accuracy_score
import joblib
import os

# === CONFIG ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, 'df_premier_features.csv')
MODEL_OUTPUT = os.path.join(SCRIPT_DIR, 'model_premier.joblib')

FEATURES = [
    'Home_Elo', 'Away_Elo',
    'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
    'Home_Streak_L5', 'Away_Streak_L5',
    'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
    'Home_Dominance', 'Away_Dominance'
]

def main():
    print("🚀 Training Dedicated Premier League Model")
    print("=" * 60)

    # 1. Load Data
    if not os.path.exists(DATA_PATH):
        print(f"❌ Data not found: {DATA_PATH}")
        return
    
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded: {len(df)} matches")
    
    # 2. Filter Valid Data
    # Ensure no 0s in critical features (simple check)
    # Actually XGBoost handles NaNs, but 0s might be meaningful "no info"
    # We proceed as is, assuming feature engineering handled NaNs.
    
    # Map Target: A=0, D=1, H=2
    # Check if 'FTR' exists
    if 'FTR' not in df.columns:
        print("❌ 'FTR' column missing")
        return
        
    df['Target'] = df['FTR'].map({'A': 0, 'D': 1, 'H': 2})
    
    # 3. Time Split
    # Train: 2010 - 2023
    # Test: 2024 (Out of sample for final check, though we want to save full model usually)
    # Ideally for production usage next season, we train on ALL available data.
    # But to validate the "Strategy", we need OOS. 
    # Let's train on 2010-2023 and report metrics on 2024.
    
    train_mask = df['Season'] <= 2023
    test_mask = df['Season'] == 2024
    
    X_train = df.loc[train_mask, FEATURES]
    y_train = df.loc[train_mask, 'Target']
    
    X_test = df.loc[test_mask, FEATURES]
    y_test = df.loc[test_mask, 'Target']
    
    print(f"Train Set: {len(X_train)} matches (2010-2023)")
    print(f"Test Set:  {len(X_test)} matches (2024)")
    
    # 4. Train Model (Calibrated XGBoost)
    # Using reasonably standard params for football
    print("\n⚙️ Training XGBoost...")
    params = {
        'n_estimators': 150,
        'max_depth': 4,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'objective': 'multi:softprob',
        'num_class': 3,
        'eval_metric': 'mlogloss',
        'random_state': 42,
        'n_jobs': -1
    }
    
    base_model = xgb.XGBClassifier(**params)
    
    # Calibrated Classifier (Isotonic)
    # CV=3 internally on X_train
    calibrated_model = CalibratedClassifierCV(base_model, method='isotonic', cv=3)
    calibrated_model.fit(X_train, y_train)
    
    # 5. Evaluate
    print("\n📊 Evaluation (Season 2024 OOS):")
    probs = calibrated_model.predict_proba(X_test)
    preds = calibrated_model.predict(X_test)
    
    loss = log_loss(y_test, probs)
    acc = accuracy_score(y_test, preds)
    
    print(f"   Log Loss: {loss:.4f} (Lower is better, < 1.05 is good)")
    print(f"   Accuracy: {acc:.2%} (Should be ~45-55%)")
    
    if acc > 0.65:
        print("⚠️ WARNING: Accuracy astonishingly high. Possible leakage still?")
    
    # 6. Save Model
    # We save the model trained on 2010-2023. 
    # (Optionally we could retrain on EVERYTHING for deployment, but for validation script we use this)
    joblib.dump(calibrated_model, MODEL_OUTPUT)
    print(f"\n💾 Model saved to: {MODEL_OUTPUT}")
    
    # Save Feature Names (hack for sklearn pipeline wrapper if needed, but joblib handles obj)
    # calibrated_model doesn't expose feature_names_in_ directly usually, 
    # but the base estimator inside does.
    # We'll attach the feature list to the object for reference if possible, 
    # or just rely on the script knowing them.
    calibrated_model.feature_names_in_ = FEATURES # Manually attach for validation script safety
    joblib.dump(calibrated_model, MODEL_OUTPUT) 

if __name__ == '__main__':
    main()
