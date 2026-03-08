import pandas as pd
import requests
import io
import os
import sys
import json
import random
import subprocess
from datetime import datetime

# Add src to path to import engine
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.dirname(BASE_DIR)) # For global src if needed

DATA_FILE = os.path.join(BASE_DIR, 'df_final_app.csv')
ODDS_FILE = os.path.join(BASE_DIR, 'data', 'live_odds.json')
URL_LATEST = "https://www.football-data.co.uk/mmz4281/2526/E0.csv" # Premier League

def download_latest_data():
    print(f"Downloading latest data from {URL_LATEST}...")
    try:
        s = requests.get(URL_LATEST, timeout=10).content
        df_new = pd.read_csv(io.StringIO(s.decode('utf-8')))
        df_new = df_new.dropna(subset=['Date', 'HomeTeam', 'AwayTeam'])
        df_new['Date'] = pd.to_datetime(df_new['Date'], dayfirst=True, errors='coerce')
        return df_new
    except Exception as e:
        print(f"Error downloading data: {e}")
        return pd.DataFrame()

def update_dataset():
    # 0. Fetch External Data (We assume FIFA/Transfermarkt don't update frequently so we skip them here, they're handled in notebook)
    print("0. Skipping External Data (Handled via scripts/)...")

    # 1. Load Existing Data
    # For Premier, we load matches_raw.csv which contains the RAW historical data
    existing_raw_file = os.path.join(BASE_DIR, 'data', 'processed', 'matches_raw.csv')
    if os.path.exists(existing_raw_file):
        print(f"Loading existing {existing_raw_file}...")
        df_old = pd.read_csv(existing_raw_file)
        df_old['Date'] = pd.to_datetime(df_old['Date'], errors='coerce')
        
        # Remove current season to avoid duplicate leakage
        cutoff_date = datetime(2025, 8, 1)
        print(f"Removing existing data from current season (Date >= {cutoff_date.date()})...")
        pre_len = len(df_old)
        df_old = df_old[df_old['Date'] < cutoff_date]
        print(f"   -> Removed {pre_len - len(df_old)} rows. Remaining history: {len(df_old)} matches.")
    else:
        print(f"Error: Could not find {existing_raw_file}. A full sync might be required.")
        df_old = pd.DataFrame()

    # 2. Download New Data
    df_new = download_latest_data()
    
    # 3. Handle Merge and Deduplicate
    df_combined = pd.DataFrame()
    if df_new.empty:
        print("No new data downloaded. Proceeding with existing data only (skipping merge).")
        df_combined = df_old
    else:
        # Save raw download
        e0_path = os.path.join(BASE_DIR, 'data', 'E0_latest.csv')
        print(f"Saving raw fresh data to {e0_path}...")
        os.makedirs(os.path.dirname(e0_path), exist_ok=True)
        try:
            df_new.to_csv(e0_path, index=False)
        except Exception as e:
            print(f"Could not save E0_latest.csv: {e}")

        print("Merging datasets...")
        cols_to_keep = ['Div','Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR','HS','AS','HST','AST','HF','AF','HC','AC','HY','AY','HR','AR']
        cols_new = [c for c in cols_to_keep if c in df_new.columns]
        df_new_clean = df_new[cols_new].copy()
        
        # Normalize team names in new data
        TEAM_MAPPING = {
            'Man United': 'Manchester United', 'Man City': 'Manchester City',
            'Spurs': 'Tottenham', 'Newcastle': 'Newcastle United',
            'Leicester': 'Leicester City', 'Norwich': 'Norwich City',
            'Leeds': 'Leeds United', 'Sheffield United': 'Sheffield Utd',
            'West Ham': 'West Ham United', 'Wolves': 'Wolverhampton Wanderers',
            'Brighton': 'Brighton & Hove Albion', 'Huddersfield': 'Huddersfield Town',
            'Cardiff': 'Cardiff City', 'Swansea': 'Swansea City',
            'Stoke': 'Stoke City', 'Hull': 'Hull City',
            'QPR': 'Queens Park Rangers', 'West Brom': 'West Bromwich Albion',
            'Bournemouth': 'AFC Bournemouth', 'Nott''m Forest': 'Nottingham Forest',
            'Luton': 'Luton Town', 'Ipswich': 'Ipswich Town'
        }
        def normalize_name(name):
            if not isinstance(name, str): return name
            return TEAM_MAPPING.get(name.strip(), name.strip())

        df_new_clean['HomeTeam'] = df_new_clean['HomeTeam'].apply(normalize_name)
        df_new_clean['AwayTeam'] = df_new_clean['AwayTeam'].apply(normalize_name)
        
        if not df_old.empty:
            df_combined = pd.concat([df_old, df_new_clean], ignore_index=True)
        else:
            df_combined = df_new_clean
            
        df_combined = df_combined.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='last').sort_values('Date')
        print(f"Total Matches after merge: {len(df_combined)}")

    # NOTE: Since feature generation for Premier is handled via scripts/4_consolidate_dataset.py
    # We will trigger that script to calculate all features and then update df_final_clean.csv.
    print("Running Feature Engineering Pipeline (4_consolidate_dataset.py)...")
    
    # Save the merged raw dataset back so the script can read it
    raw_merged_path = os.path.join(BASE_DIR, 'data', 'processed', 'matches_raw.csv')
    os.makedirs(os.path.dirname(raw_merged_path), exist_ok=True)
    df_combined.to_csv(raw_merged_path, index=False)
    
    try:
        fe_script = os.path.join(BASE_DIR, "scripts", "4_consolidate_dataset.py")
        subprocess.run([sys.executable, fe_script], check=True, cwd=BASE_DIR)
        
        # 4_consolidate_dataset.py creates 'df_premier_complete.csv'
        complete_csv = os.path.join(BASE_DIR, 'data', 'processed', 'df_premier_complete.csv')
        if os.path.exists(complete_csv):
            print("Mapping consolidated dataset to df_final_clean.csv format...")
            df_comp = pd.read_csv(complete_csv)
            # rename columns to match what notebooks/V3 outputs and app expects
            mapping = {
                'Home_Team': 'HomeTeam', 
                'Away_Team': 'AwayTeam',
            }
            df_comp = df_comp.rename(columns=mapping)
            
            # The app needs Season but 4_consolidate_dataset doesn't output it explicitly, let's derive it
            if 'Date' in df_comp.columns:
                df_comp['Date'] = pd.to_datetime(df_comp['Date'])
                df_comp['Season'] = df_comp['Date'].apply(lambda d: d.year if d.month > 7 else d.year - 1)
            
            # target extraction
            target_map = {'A': 0, 'D': 1, 'H': 2}
            df_comp['Target'] = df_comp['FTR'].map(target_map)
            
            
            # Since existing_data_file variable was removed above, we must define it
            existing_data_file = os.path.join(BASE_DIR, 'notebooks', 'df_final_clean.csv')
            df_comp.to_csv(existing_data_file, index=False)
            print(f"✅ df_final_clean.csv updated successfully with new engineered features ({len(df_comp)} matches)!")
        else:
            print("⚠️ Warning: df_premier_complete.csv was not generated.")
            
    except subprocess.CalledProcessError as e:
        print(f"Error running feature engineering pipeline: {e}")
    except Exception as e:
        print(f"Unexpected error in feature engineering: {e}")

    # --------------------------------------------------------------------------
    # 4. Run Scraper for Live Odds
    # --------------------------------------------------------------------------
    print("\n[4/4] Fetching Live Odds from Winamax...")
    try:
        print("   -> Launching Puppeteer Scraper (Step 1: Extract)...")
        scrape_script = os.path.join(BASE_DIR, "src", "scraper_winamax.js")
        subprocess.run(["node", scrape_script], check=True, shell=True, cwd=BASE_DIR)
        
        print("   -> Processing extracted state (Step 2: Parse)...")
        process_script = os.path.join(BASE_DIR, "src", "process_state.py")
        subprocess.run([sys.executable, process_script], check=True, shell=True, cwd=BASE_DIR)
        
        print("   -> Live odds updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running scraper pipeline: {e}")
    except Exception as e:
        print(f"Unexpected error in scraping: {e}")

    print("\nUpdate Process Completed Successfully!")

if __name__ == "__main__":
    update_dataset()
