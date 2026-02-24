import pandas as pd
import json
import os

df = pd.read_csv('../df_final_app.csv')
print('Distinct seasons in df:', df['Season'].unique())

with open('../data/sofifa_history.json', 'r', encoding='utf-8') as f:
    sofifa_data = json.load(f)

print('Sofifa keys:', list(sofifa_data.keys()))

with open('../data/transfermarkt_history.json', 'r', encoding='utf-8') as f:
    tm_data = json.load(f)

print('TM keys:', list(tm_data.keys()))
