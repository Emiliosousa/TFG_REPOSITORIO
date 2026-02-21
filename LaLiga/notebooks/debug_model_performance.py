import pandas as pd
import numpy as np
import joblib
import os
import xgboost

def debug_model():
    print("DEBUGGING MODEL PREDICTIONS")
    
    # Paths
    data_path = '../../Premier/df_premier_features.csv'
    model_path = '../../LaLiga/modelo_city_group.joblib'
    
    if not os.path.exists(data_path):
        print("Data not found")
        return
        
    df = pd.read_csv(data_path)
    model = joblib.load(model_path)
    
    # Features
    features = [
        'Home_Elo', 'Away_Elo', 
        'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
        'Home_Streak_L5', 'Away_Streak_L5',
        'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
        'Home_Dominance', 'Away_Dominance'
    ]
    
    # Check if features exist
    missing = [c for c in features if c not in df.columns]
    if missing:
        print(f"Missing features: {missing}")
        return

    X = df[features]
    y = df['FTR'].map({'A': 0, 'D': 1, 'H': 2})
    
    print("Predicting...")
    try:
        probs = model.predict_proba(X)
        preds = model.predict(X)
    except Exception as e:
        print(f"Prediction failed: {e}")
        return
        
    # Analysis
    acc = np.mean(preds == y)
    print(f"Accuracy on Premier Data: {acc:.4f}")
    
    if acc > 0.8:
        print("🚨 LEAK CONFIRMED! Accuracy > 80% is impossible for football.")
    else:
        print("Accuracy seems normal (45-55%). Leak might be subtle or financial only.")
        
    # Feature Importance (if possible)
    try:
        print("Feature Importances:")
        imps = model.feature_importances_
        for name, imp in zip(features, imps):
            print(f"  {name}: {imp:.4f}")
    except:
        pass

    # Check correlation of Top Feature with Target
    top_feature_idx = np.argmax(imps)
    top_feature_name = features[top_feature_idx]
    
    print(f"\nChecking Top Feature '{top_feature_name}' correlation with Target...")
    # Map target to numeric for correlation
    # Target 2 (Home) vs 0 (Away). 1 (Draw) is noise.
    # Let's check Home Win vs feature
    
    df['Target_Num'] = y
    corr = df[top_feature_name].corr(df['Target_Num'])
    print(f"Correlation: {corr:.4f}")
    
    if abs(corr) > 0.6:
        print("🚨 HIGH CORRELATION detected in Top Feature!")

if __name__ == "__main__":
    debug_model()
