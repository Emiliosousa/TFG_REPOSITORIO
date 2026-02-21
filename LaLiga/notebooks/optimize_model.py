
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import log_loss, accuracy_score
import optuna
import joblib
import os

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

DATA_FILE = r'C:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\df_final_app.csv'
MODEL_FILE = r'C:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\modelo_city_group_optimized.joblib'

def objective(trial):
    # Load Data (Cached if possible in real scenarion, but here we load each time or global)
    df = pd.read_csv(DATA_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').dropna(subset=['FTR', 'B365H', 'B365D', 'B365A'])
    
    # Features (Rich Set)
    features = [
        'Home_Elo', 'Away_Elo',
        'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
        'Home_Streak_L5', 'Away_Streak_L5',
        'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
        'Home_Dominance_Avg_L5', 'Away_Dominance_Avg_L5',
        'Home_FIFA_Ova', 'Away_FIFA_Ova',
        'Diff_FIFA_Ova', 'Diff_FIFA_Att', 'Diff_FIFA_Mid', 'Diff_FIFA_Def',
        'Log_Value_Diff'
    ]
    
    # Filter features that exist
    features = [f for f in features if f in df.columns]

    # Time Split
    # Train: < 2024-08-01
    # Val: >= 2024-08-01 (Using 2025 as validation set for optimization)
    split_date = '2024-08-01'
    
    train = df[df['Date'] < split_date]
    val = df[df['Date'] >= split_date]
    
    X_train = train[features]
    y_train = train['FTR'].map({'H': 2, 'D': 1, 'A': 0})
    X_val = val[features]
    y_val = val['FTR'].map({'H': 2, 'D': 1, 'A': 0})
    
    # Hyperparameters
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 2, 8),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'gamma': trial.suggest_float('gamma', 0, 5),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'reg_alpha': trial.suggest_float('reg_alpha', 0, 10),
        'reg_lambda': trial.suggest_float('reg_lambda', 0, 10),
        'objective': 'multi:softprob',
        'num_class': 3,
        'random_state': 42,
        'n_jobs': -1
    }
    
    model = xgb.XGBClassifier(**params)
    
    # Fit
    model.fit(X_train, y_train, verbose=False)
    
    # Predict
    probs = model.predict_proba(X_val)
    
    # Calculate LogLoss (for stability)
    ll = log_loss(y_val, probs)
    
    # Calculate ROI (for profitability)
    # Strategy: Bet on highest EV > 0.05
    val['Prob_A'] = probs[:, 0]
    val['Prob_D'] = probs[:, 1]
    val['Prob_H'] = probs[:, 2]
    
    profit = 0
    bets = 0
    stake = 1
    
    for idx, row in val.iterrows():
        # Odds
        oh, od, oa = row['B365H'], row['B365D'], row['B365A']
        ph, pd_prob, pa = row['Prob_H'], row['Prob_D'], row['Prob_A']
        
        evs = {'H': (ph*oh)-1, 'D': (pd_prob*od)-1, 'A': (pa*oa)-1}
        best_bet = max(evs, key=evs.get)
        best_ev = evs[best_bet]
        
        if best_ev > 0.05: # Threshold
            bets += 1
            if row['FTR'] == best_bet:
                odds = oh if best_bet == 'H' else (od if best_bet == 'D' else oa)
                profit += (odds - 1) * stake
            else:
                profit -= stake
                
    roi = (profit / bets) * 100 if bets > 20 else -100 # Penalize low volume
    
    # Optimization Goal: Maximize ROI (Primary) and Minimize LogLoss (Secondary implicit)
    # We return ROI. Optuna maximizes by default? No, maximize/minimize direction set in study.
    return roi

def run_optimization():
    print("🚀 Starting Optuna Optimization for ROI...")
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=50) 
    
    print("\n✅ Optimization Complete!")
    print("Best ROI:", study.best_value)
    print("Best Params:", study.best_params)
    
    # Train final model with best params
    print("\nSaving Best Model...")
    
    # Re-load full data (or train/test)
    df = pd.read_csv(DATA_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').dropna(subset=['FTR'])
    
    features = [
        'Home_Elo', 'Away_Elo',
        'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
        'Home_Streak_L5', 'Away_Streak_L5',
        'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
        'Home_Dominance_Avg_L5', 'Away_Dominance_Avg_L5',
        'Home_FIFA_Ova', 'Away_FIFA_Ova',
        'Diff_FIFA_Ova', 'Diff_FIFA_Att', 'Diff_FIFA_Mid', 'Diff_FIFA_Def',
        'Log_Value_Diff'
    ]
    features = [f for f in features if f in df.columns]
    
    # Use split date again to ensure comparable test
    split_date = '2024-08-01'
    train = df[df['Date'] < split_date]
    
    X_train = train[features]
    y_train = train['FTR'].map({'H': 2, 'D': 1, 'A': 0})
    
    best_params = study.best_params
    best_params['objective'] = 'multi:softprob'
    best_params['num_class'] = 3
    
    final_model = xgb.XGBClassifier(**best_params)
    final_model.fit(X_train, y_train)
    
    joblib.dump(final_model, MODEL_FILE)
    print(f"Model saved to {MODEL_FILE}")

if __name__ == "__main__":
    run_optimization()
