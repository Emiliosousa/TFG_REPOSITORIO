import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
import os

# === CONFIG ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, 'df_premier_features.csv')

FEATURES = [
    'Home_Elo', 'Away_Elo', 
    'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
    'Home_Streak_L5', 'Away_Streak_L5',
    'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
    'Home_Dominance', 'Away_Dominance'
]

def main():
    print("🚀 Premier League Strategy Validation (Walk-Forward)")
    print("=" * 60)

    # 1. Load Data
    if not os.path.exists(DATA_PATH):
        print(f"❌ Data file not found: {DATA_PATH}")
        return

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded: {len(df)} matches")
    
    if 'B365H' not in df.columns:
        print("❌ Odds missing")
        return

    # Target Mapping
    df['Target'] = df['FTR'].map({'A': 0, 'D': 1, 'H': 2})
    
    # 2. Walk-Forward Configuration
    # We need a few years to train. Let's start training on 2010-2015, test 2016...
    # Or just test last 4 seasons as requested: 2021, 2022, 2023, 2024.
    # Train on 2010-2020 for first fold.
    
    test_seasons = [2021, 2022, 2023, 2024]
    
    # Store predictions
    all_preds_df = pd.DataFrame()
    
    print("\n⚙️ Starting Walk-Forward Loop...")
    
    for season in test_seasons:
        print(f"\n  Processing Season {season}...")
        
        # Split
        train_mask = df['Season'] < season
        test_mask = df['Season'] == season
        
        X_train = df.loc[train_mask, FEATURES]
        y_train = df.loc[train_mask, 'Target']
        
        X_test = df.loc[test_mask, FEATURES]
        y_test = df.loc[test_mask, 'Target']
        
        if len(X_test) == 0:
            print("    No games found.")
            continue
            
        # Train
        params = {
            'n_estimators': 100, # Faster for loop
            'max_depth': 4,
            'learning_rate': 0.05,
            'objective': 'multi:softprob',
            'num_class': 3,
            'eval_metric': 'mlogloss',
            'random_state': 42,
            'n_jobs': -1
        }
        base = xgb.XGBClassifier(**params)
        calib = CalibratedClassifierCV(base, method='isotonic', cv=3)
        calib.fit(X_train, y_train)
        
        # Predict
        probs = calib.predict_proba(X_test)
        
        # Store
        subset = df.loc[test_mask].copy()
        subset['Prob_A'] = probs[:, 0]
        subset['Prob_D'] = probs[:, 1]
        subset['Prob_H'] = probs[:, 2]
        
        all_preds_df = pd.concat([all_preds_df, subset])
        print(f"    Predictions generated for {len(subset)} matches.")

    # 3. Strategy Analysis
    print("\n💰 Analyzing Strategy Performance (OOS Data Only)...")
    
    ev_thresholds = [0.03, 0.05, 0.10]
    kelly_fractions = [0.1, 0.25]
    max_odds = 5.0  # Strict Filter
    min_odds = 1.2
    
    results = []
    
    best_roi = -999
    
    for ev_thresh in ev_thresholds:
        for kelly in kelly_fractions:
            
            total_profit = 0
            total_staked = 0
            bets_placed = 0
            wins = 0
            
            # Iterate through predicted matches
            # EV = (Prob * Odds) - 1
            # Best Bet per match
            
            # Vectorized calc for speed
            odds = all_preds_df[['B365A', 'B365D', 'B365H']].values
            probs = all_preds_df[['Prob_A', 'Prob_D', 'Prob_H']].values
            outcomes = all_preds_df['Target'].values
            
            ev_matrix = (probs * odds) - 1
            
            # Max EV per match
            best_idx = np.argmax(ev_matrix, axis=1)
            best_ev = np.max(ev_matrix, axis=1)
            
            # Helper to select from 2D array by index
            # odds[row, col]
            row_idx = np.arange(len(odds))
            best_odds = odds[row_idx, best_idx]
            best_prob = probs[row_idx, best_idx]
            
            # Filters
            mask = (best_ev >= ev_thresh) & (best_odds <= max_odds) & (best_odds >= min_odds)
            
            # Kelly Fraction
            b = best_odds[mask] - 1
            p = best_prob[mask]
            q = 1 - p
            f = (b * p - q) / b
            f = f * kelly
            f = np.clip(f, 0.0, 0.05)
            
            # Results
            # Did we win?
            # outcome is 0,1,2. best_idx is 0,1,2.
            bet_won = (outcomes[mask] == best_idx[mask])
            
            # PnL
            # Win: f * b
            # Lose: -f
            pnl = np.where(bet_won, f * b, -f)
            
            total_profit = pnl.sum()
            total_staked = f.sum()
            bets_placed = len(f)
            wins = bet_won.sum()
            
            roi = (total_profit / total_staked) if total_staked > 0 else 0
            wr = (wins / bets_placed) if bets_placed > 0 else 0
            
            results.append({
                'EV': ev_thresh,
                'Kelly': kelly,
                'ROI': roi,
                'Bets': bets_placed,
                'WinRate': wr,
                'Profit_Units': total_profit
            })
            
            if roi > best_roi:
                best_roi = roi

    # Summary
    print("\nFINAL VALIDATION RESULTS (2021-2024)")
    print("-" * 60)
    res_df = pd.DataFrame(results)
    print(res_df.sort_values('ROI', ascending=False))
    
    res_df.to_csv('validation_walkforward_summary.csv', index=False)
    print("\n✅ Results saved to validation_walkforward_summary.csv")

if __name__ == '__main__':
    main()
