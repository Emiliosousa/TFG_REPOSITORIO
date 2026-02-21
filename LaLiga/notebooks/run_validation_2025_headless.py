
import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
from sklearn.metrics import log_loss, accuracy_score, classification_report
import os
import sys

# Constants
DATA_FILE = r'C:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\df_final_app.csv'

def run_validation():
    print("RUNNING 2025 VALIDATION (HEADLESS)...")
    
    if not os.path.exists(DATA_FILE):
        print(f"❌ Data file not found: {DATA_FILE}")
        return

    df = pd.read_csv(DATA_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    print(f"Loaded {len(df)} matches.")
    
    # Features (Updated with Alpha)
    features = [
        # Elo
        'Home_Elo', 'Away_Elo',
        # Rolling Performance
        'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
        'Home_Streak_L5', 'Away_Streak_L5',
        'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
        'Home_Dominance_Avg_L5', 'Away_Dominance_Avg_L5',
        # --- NEW ALPHA (FIFA/TM) ---
        'Home_FIFA_Ova', 'Away_FIFA_Ova',
        'Diff_FIFA_Ova', 'Diff_FIFA_Att', 'Diff_FIFA_Mid', 'Diff_FIFA_Def',
        'Log_Value_Diff'
    ]
    
    # Check for missing features
    missing = [f for f in features if f not in df.columns]
    if missing:
        print(f"❌ Missing features: {missing}")
        return

    # Train/Test Split (Time Based)
    # Train: < 2024-08-01 (End of 23/24 season)
    # Test: >= 2024-08-01 (Start of 24/25 season - "2025" in user terms)
    
    split_date = '2024-08-01'
    
    train = df[df['Date'] < split_date].copy()
    test = df[df['Date'] >= split_date].copy()
    
    # Filter only finished matches for training
    train = train.dropna(subset=['FTR'])
    test = test.dropna(subset=['FTR']) # Validate on finished games
    
    print(f"Train Set: {len(train)} matches (Up to {split_date})")
    print(f"Test Set: {len(test)} matches (From {split_date})")
    
    if test.empty:
        print("❌ Test set is empty. Cannot validate 2025.")
        return

    # Target
    train['Target_Num'] = train['FTR'].map({'H': 2, 'D': 1, 'A': 0})
    test['Target_Num'] = test['FTR'].map({'H': 2, 'D': 1, 'A': 0})
    
    X_train = train[features]
    y_train = train['Target_Num']
    X_test = test[features]
    y_test = test['Target_Num']
    
    # Model (XGBoost) - Same params as notebook if possible, or standard
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.05,
        objective='multi:softprob',
        num_class=3,
        random_state=42,
        eval_metric='mlogloss'
    )
    
    print("Training XGBoost...")
    model.fit(X_train, y_train)
    
    # Predict
    probs = model.predict_proba(X_test)
    preds = model.predict(X_test)
    
    # Metrics
    acc = accuracy_score(y_test, preds)
    ll = log_loss(y_test, probs)
    print(f"\n--- MODEL METRICS (OOS 2025) ---")
    print(f"Accuracy: {acc:.2%}")
    print(f"Log Loss: {ll:.4f}")
    
    # --- FINANCIAL BACKTEST ---
    print("\n--- BETTING STRATEGY BACKTEST ---")
    
    # Add probs to test df
    test['Prob_A'] = probs[:, 0]
    test['Prob_D'] = probs[:, 1]
    test['Prob_H'] = probs[:, 2]
    
    # Odds (Handle missing columns)
    if 'B365H' not in test.columns:
        print("⚠️ Outcomes missing odds (B365H/D/A). Cannot backtest.")
        return

    initial_bank = 1000
    current_bank = initial_bank
    stake_fixed = 10 # Flat stake
    
    bets_placed = 0
    wins = 0
    profit = 0
    
    # EV Threshold
    EV_THRESH = 0.05
    
    for idx, row in test.iterrows():
        # Odds
        oh = row.get('B365H', 1.0)
        od = row.get('B365D', 1.0)
        oa = row.get('B365A', 1.0)
        
        # Probs
        ph = row['Prob_H']
        pd_prob = row['Prob_D']
        pa = row['Prob_A']
        
        # EV
        ev_h = (ph * oh) - 1
        ev_d = (pd_prob * od) - 1
        ev_a = (pa * oa) - 1
        
        # Select Best Bet
        best_ev = max(ev_h, ev_d, ev_a)
        
        if best_ev > EV_THRESH:
            bets_placed += 1
            bet_on = None
            bet_odds = 0
            
            if best_ev == ev_h:
                bet_on = 'H'
                bet_odds = oh
            elif best_ev == ev_d:
                bet_on = 'D'
                bet_odds = od
            else:
                bet_on = 'A'
                bet_odds = oa
                
            # Check Result
            won = (row['FTR'] == bet_on)
            
            if won:
                wins += 1
                pnl = stake_fixed * (bet_odds - 1)
            else:
                pnl = -stake_fixed
                
            profit += pnl
            current_bank += pnl
            
    roi = (profit / (bets_placed * stake_fixed)) * 100 if bets_placed > 0 else 0
    
    print(f"Bets Placed: {bets_placed}")
    print(f"Wins: {wins} ({wins/bets_placed:.1%})")
    print(f"Profit: {profit:.2f}u")
    print(f"ROI: {roi:.2f}%")
    print(f"Final Bank: {current_bank:.2f}u")
    
    if abs(roi) > 50:
        print("\n🚨 WARNING: ROI still anomalously high/low. Check for remaining leakage.")
    else:
        print("\n✅ RESULT: ROI seems realistic.")

if __name__ == "__main__":
    run_validation()
