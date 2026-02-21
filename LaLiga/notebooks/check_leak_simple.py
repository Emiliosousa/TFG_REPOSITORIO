import csv
import os

def check_csv(filepath):
    print(f"\nChecking {filepath}...")
    if not os.path.exists(filepath):
        print("File not found")
        return

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        if 'Home_xG_Proxy' not in headers or 'Home_xG_Avg_L5' not in headers:
            print(f"Skipping: Columns missing. Headers: {headers[:5]}...")
            return

        leaks = 0
        rows = 0
        for row in reader:
            rows += 1
            try:
                xg = float(row['Home_xG_Proxy']) if row['Home_xG_Proxy'] else 0
                l5 = float(row['Home_xG_Avg_L5']) if row['Home_xG_Avg_L5'] else 0
                
                # Check for exact match (very suspicious if happens often, unless both are 0)
                if xg == l5 and xg > 0:
                    leaks += 1
            except ValueError:
                continue
                
        print(f"Total Rows: {rows}")
        print(f"Exact matches (xg == l5 > 0): {leaks}")
        if leaks > rows * 0.1:
            print("🚨 HIGH LEAKAGE DETECTED! Avg_L5 equals current match xG")
        else:
            print("✅ No direct xG leak found.")

check_csv('df_final_clean.csv')
check_csv('../df_final_app.csv')
