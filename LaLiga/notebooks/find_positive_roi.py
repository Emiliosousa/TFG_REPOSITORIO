
import pandas as pd
import joblib
import numpy as np

# Load Data
df = pd.read_csv('../df_final_app.csv')
df['Date'] = pd.to_datetime(df['Date'])
val = df[df['Date'] >= '2024-08-01'].copy().sort_values('Date')

# Features (Must match training)
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

# Load Optimized Model
model = joblib.load('../modelo_city_group_optimized.joblib')

# Predict
X_val = val[features]
probs = model.predict_proba(X_val)

val['Prob_A'] = probs[:, 0]
val['Prob_D'] = probs[:, 1]
val['Prob_H'] = probs[:, 2]

print(f"Searching for Profitable Threshold on {len(val)} matches...")
print("-" * 65)
print(f"{'Threshold':<10} | {'Bets':<5} | {'Win Rate':<10} | {'Profit':<10} | {'ROI':<10}")
print("-" * 65)

results_list = []
header = f"{'Threshold':<10} | {'Bets':<5} | {'Win Rate':<10} | {'Profit':<10} | {'ROI':<10}"
results_list.append(header)

stake = 1

# Test thresholds from 0.00 to 0.15
for threshold in np.arange(0.00, 0.16, 0.01):
    profit = 0
    bets = 0
    wins = 0
    
    for idx, row in val.iterrows():
        oh, od, oa = row['B365H'], row['B365D'], row['B365A']
        ph, pd_prob, pa = row['Prob_H'], row['Prob_D'], row['Prob_A']
        
        # EV Calculation
        evs = {'H': (ph*oh)-1, 'D': (pd_prob*od)-1, 'A': (pa*oa)-1}
        best_bet = max(evs, key=evs.get)
        best_ev = evs[best_bet]
        
        # Check Value Threshold (Edge > threshold)
        # Edge = Model_Prob - Implied_Prob
        # Implied_Prob = 1/Odds
        # Value = Model_Prob - (1/Odds) ---> Wait, EV > X is standard, but user asked for "Value Filter"
        # Let's stick to EV > Threshold as it's cleaner financially.
        # EV = (Prob * Odds) - 1. So EV > 0.05 means ROI expectation > 5%.
        
        if best_ev > threshold:
            bets += 1
            if row['FTR'] == best_bet:
                odds = oh if best_bet == 'H' else (od if best_bet == 'D' else oa)
                profit += (odds - 1) * stake
                wins += 1
            else:
                profit -= stake

    roi = (profit / bets) * 100 if bets > 0 else 0
    win_rate = (wins / bets) * 100 if bets > 0 else 0
    
    line = f"{threshold:<10.2f} | {bets:<5} | {win_rate:<9.1f}% | {profit:<9.2f}u | {roi:<9.2f}%"
    print(line)
    results_list.append(line)

with open('roi_thresholds.txt', 'w') as f:
    f.write("\n".join(results_list))
print("\nResults saved to roi_thresholds.txt")
