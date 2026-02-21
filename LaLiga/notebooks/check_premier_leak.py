import csv
import os

def check_csv(filepath):
    print(f"\nChecking {filepath}...")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Check available columns
        print(f"Columns: {headers[:5]} ...")
        
        # Expected xG columns
        xg_curr = 'Home_xG' if 'Home_xG' in headers else ('Home_xG_Proxy' if 'Home_xG_Proxy' in headers else None)
        xg_roll = 'Home_xG_Avg_L5'
        
        if not xg_curr or xg_roll not in headers:
            print(f"Skipping xG check: Columns missing. Found: {xg_curr}, {xg_roll}")
        else:
            print(f"Comparing {xg_curr} vs {xg_roll}...")
            leaks = 0
            rows = 0
            for row in reader:
                rows += 1
                try:
                    xg = float(row[xg_curr]) if row[xg_curr] else 0
                    l5 = float(row[xg_roll]) if row[xg_roll] else 0
                    if xg == l5 and xg > 0:
                        leaks += 1
                except ValueError:
                    continue
            print(f"Total Rows: {rows}")
            print(f"Direct Leaks (Current == Avg): {leaks}")

# Check Premier file
check_csv('../../Premier/df_premier_features.csv')
