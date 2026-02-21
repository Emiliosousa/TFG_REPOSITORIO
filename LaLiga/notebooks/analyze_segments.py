
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

# Prepare Results List
results = []

def get_odds_bucket(o):
    if o < 1.5: return '1.0 - 1.5'
    if o < 2.0: return '1.5 - 2.0'
    if o < 2.5: return '2.0 - 2.5'
    if o < 3.0: return '2.5 - 3.0'
    if o < 4.0: return '3.0 - 4.0'
    return '4.0 +'

for idx, row in val.iterrows():
    oh, od, oa = row['B365H'], row['B365D'], row['B365A']
    ph, pd_prob, pa = row['Prob_H'], row['Prob_D'], row['Prob_A']
    
    # EV Calculation
    evs = {'H': (ph*oh)-1, 'D': (pd_prob*od)-1, 'A': (pa*oa)-1}
    best_bet = max(evs, key=evs.get)
    best_ev = evs[best_bet]
    
    # Only consider "Value" bets (> 0.05 EV) as baseline candidates
    if best_ev > 0.05:
        odds = oh if best_bet == 'H' else (od if best_bet == 'D' else oa)
        bucket = get_odds_bucket(odds)
        
        profit = -1
        won = False
        if row['FTR'] == best_bet:
            profit = (odds - 1)
            won = True
            
        results.append({
            'Bet': best_bet,
            'Odds Bucket': bucket,
            'Profit': profit,
            'Won': won
        })

res_df = pd.DataFrame(results)

print("\n--- ROI BY SEGMENT (EV > 0.05) ---")
# Pivot Table
pivot = res_df.groupby(['Bet', 'Odds Bucket']).agg({
    'Profit': 'sum',
    'Won': ['count', 'mean']
})

# Flatten cols
pivot.columns = ['Profit', 'Bets', 'Win Rate']
pivot['ROI'] = (pivot['Profit'] / pivot['Bets']) * 100
pivot['Win Rate'] = pivot['Win Rate'] * 100

print(pivot)

# Save to file
pivot.to_csv('segment_analysis.csv')
print("\nSaved to segment_analysis.csv")
