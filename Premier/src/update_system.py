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
    # For Premier, we load df_final_clean.csv from notebooks (v3) as the authoritative source
    existing_data_file = os.path.join(BASE_DIR, 'notebooks', 'df_final_clean.csv')
    if os.path.exists(existing_data_file):
        print(f"Loading existing {existing_data_file}...")
        df_old = pd.read_csv(existing_data_file)
        df_old['Date'] = pd.to_datetime(df_old['Date'])
        
        # --- LEAKAGE FIX: STRIP ENGINEERED COLUMNS ---
        raw_cols = ['Div','Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR','HS','AS','HST','AST','HF','AF','HC','AC','HY','AY','HR','AR','B365H','B365D','B365A','Season']
        keep_cols = [c for c in raw_cols if c in df_old.columns]
        print(f"   -> Stripping engineered features. Keeping {len(keep_cols)} raw columns.")
        df_old = df_old[keep_cols].copy()

        # Remove current season to avoid duplicate leakage
        cutoff_date = datetime(2025, 8, 1)
        print(f"Removing existing data from current season (Date >= {cutoff_date.date()})...")
        pre_len = len(df_old)
        df_old = df_old[df_old['Date'] < cutoff_date]
        print(f"   -> Removed {pre_len - len(df_old)} rows. Remaining history: {len(df_old)} matches.")
    else:
        print(f"Error: Could not find {existing_data_file}.")
        df_old = pd.DataFrame()

    # 2. Download New Data
    df_new = download_latest_data()
    
    if df_new.empty:
        print("No new data downloaded. Proceeding with existing data only (skipping merge).")
    else:
        # Save raw download
        e0_path = os.path.join(BASE_DIR, 'data', 'E0_latest.csv')
        print(f"Saving raw fresh data to {e0_path}...")
        os.makedirs(os.path.dirname(e0_path), exist_ok=True)
        try:
            df_new.to_csv(e0_path, index=False)
        except Exception as e:
            print(f"Could not save E0_latest.csv: {e}")

        # 3. Merge and Deduplicate
        print("Merging datasets...")
        cols_to_keep = ['Div','Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR','HS','AS','HST','AST','HF','AF','HC','AC','HY','AY','HR','AR']
        cols_new = [c for c in cols_to_keep if c in df_new.columns]
        df_new_clean = df_new[cols_new].copy()
        
        if not df_old.empty:
            df_combined = pd.concat([df_old, df_new_clean], ignore_index=True)
        else:
            df_combined = df_new_clean
            
        df_combined = df_combined.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='last').sort_values('Date')
        print(f"Total Matches after merge: {len(df_combined)}")

    # NOTE: Since feature generation for Premier is handled exclusively via the V3 notebooks right now
    # We will log that the user needs to re-run Notebook 01 for full feature engineering of the new data.
    print("NOTE: Feature engineering for Premier League is currently integrated via Notebook 01_Ingenieria_de_Datos_v3.ipynb.")
    print("New matches have been downloaded, but please render the notebook to update the app's internal features fully.")

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
