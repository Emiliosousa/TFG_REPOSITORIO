
import pandas as pd
import joblib
import numpy as np

# Load Data
df = pd.read_csv('../df_final_app.csv')
df['Date'] = pd.to_datetime(df['Date'])
val = df[df['Date'] >= '2024-08-01'].copy().sort_values('Date')

# Features
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

model = joblib.load('../modelo_city_group_optimized.joblib')

# Predict
X_val = val[features]
probs = model.predict_proba(X_val)

val['Prob_A'] = probs[:, 0]
val['Prob_D'] = probs[:, 1]
val['Prob_H'] = probs[:, 2]

profit = 0
bets = 0
wins = 0
stake = 1

results = []

print("Running Composite Filter Strategy...")
print("1. Home: Odds <= 2.0")
print("2. Away: Odds <= 3.0 (and > 1.5)")
print("3. Draw: Odds >= 3.0")
print("-" * 30)

for idx, row in val.iterrows():
    oh, od, oa = row['B365H'], row['B365D'], row['B365A']
    ph, pd_prob, pa = row['Prob_H'], row['Prob_D'], row['Prob_A']
    
    # EV Calculation
    evs = {'H': (ph*oh)-1, 'D': (pd_prob*od)-1, 'A': (pa*oa)-1}
    best_bet = max(evs, key=evs.get)
    best_ev = evs[best_bet]
    
    # Base Value Check
    if best_ev > 0.05:
        odds = oh if best_bet == 'H' else (od if best_bet == 'D' else oa)
        
        # --- COMPOSITE FILTER ---
        allowed = False
        
        if best_bet == 'H':
            if odds <= 2.0: allowed = True
            
        elif best_bet == 'A':
            if 1.5 <= odds <= 3.0: allowed = True
            
        elif best_bet == 'D':
            if odds >= 3.0: allowed = True
            
        if allowed:
            bets += 1
            pnl = -stake
            is_win = False
            
            if row['FTR'] == best_bet:
                pnl = (odds - 1) * stake
                wins += 1
                is_win = True
            
            profit += pnl
            results.append({'Match': f"{row['HomeTeam']} vs {row['AwayTeam']}", 'Bet': best_bet, 'Odds': odds, 'Profit': pnl})

roi = (profit / bets) * 100 if bets > 0 else 0
win_rate = (wins / bets) * 100 if bets > 0 else 0

print(f"Bets: {bets}")
print(f"Profit: {profit:.2f}u")
print(f"ROI: {roi:.2f}%")
print(f"Win Rate: {win_rate:.2f}%")

# Save detailed results
res_df = pd.DataFrame(results)
res_df.to_csv('composite_results.csv', index=False)
