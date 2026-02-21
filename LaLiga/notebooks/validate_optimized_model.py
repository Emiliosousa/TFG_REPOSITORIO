
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

# Load Model
model = joblib.load('../modelo_city_group_optimized.joblib')

# Predict
X_val = val[features]
probs = model.predict_proba(X_val)

val['Prob_A'] = probs[:, 0]
val['Prob_D'] = probs[:, 1]
val['Prob_H'] = probs[:, 2]

# Evaluate ROI
profit = 0
bets = 0
stake = 1

print(f"Validating Optimized Model on {len(val)} matches...")

results = []

for idx, row in val.iterrows():
    oh, od, oa = row['B365H'], row['B365D'], row['B365A']
    ph, pd_prob, pa = row['Prob_H'], row['Prob_D'], row['Prob_A']
    
    # EV Calculation
    evs = {'H': (ph*oh)-1, 'D': (pd_prob*od)-1, 'A': (pa*oa)-1}
    best_bet = max(evs, key=evs.get)
    best_ev = evs[best_bet]
    
    if best_ev > 0.05: # Same threshold as optimization
        bets += 1
        won = False
        pnl = -stake
        if row['FTR'] == best_bet:
            odds = oh if best_bet == 'H' else (od if best_bet == 'D' else oa)
            pnl = (odds - 1) * stake
            won = True
            
        profit += pnl
        results.append({
            'Date': row['Date'],
            'Match': f"{row['HomeTeam']} vs {row['AwayTeam']}",
            'Bet': best_bet,
            'Odds': oh if best_bet == 'H' else (od if best_bet == 'D' else oa),
            'Result': row['FTR'],
            'Won': won,
            'Profit': pnl
        })

roi = (profit / bets) * 100 if bets > 0 else 0
win_rate = (sum([1 for r in results if r['Won']]) / bets) * 100 if bets > 0 else 0

print("\n--- OPTIMIZED RESULTS ---")
print(f"Bets: {bets}")
print(f"Profit: {profit:.2f}u")
print(f"ROI: {roi:.2f}%")
print(f"Win Rate: {win_rate:.2f}%")

# Save detailed results
res_df = pd.DataFrame(results)
res_df.to_csv('optimized_results_2025.csv', index=False)
print("\nDetailed results saved to optimized_results_2025.csv")
