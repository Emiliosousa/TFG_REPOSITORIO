
import pandas as pd

try:
    df = pd.read_csv('optimized_results_2025.csv')
    bets = len(df)
    profit = df['Profit'].sum()
    roi = (profit / bets) * 100 if bets > 0 else 0
    win_rate = (df['Won'].sum() / bets) * 100 if bets > 0 else 0
    
    print(f"Bets: {bets}")
    print(f"Profit: {profit:.2f}u")
    print(f"ROI: {roi:.2f}%")
    print(f"Win Rate: {win_rate:.2f}%")
except Exception as e:
    print(f"Error reading results: {e}")
