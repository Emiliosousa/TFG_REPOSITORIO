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
try:
    from src.feature_engineering import generate_features
except ImportError:
    # Fallback if running from src directory
    sys.path.append(os.path.dirname(os.getcwd()))
    from src.feature_engineering import generate_features

DATA_FILE = os.path.join(BASE_DIR, 'df_final_app.csv')
ODDS_FILE = os.path.join(BASE_DIR, 'data', 'live_odds.json')
URL_2425 = "https://www.football-data.co.uk/mmz4281/2425/SP1.csv"

def download_latest_data():
    print(f"⬇️ Downloading latest data from {URL_2425}...")
    try:
        s = requests.get(URL_2425, timeout=10).content
        df_new = pd.read_csv(io.StringIO(s.decode('utf-8')))
        # Clean columns usually found in football-data
        df_new = df_new.dropna(subset=['Date', 'HomeTeam', 'AwayTeam'])
        df_new['Date'] = pd.to_datetime(df_new['Date'], dayfirst=True, errors='coerce')
        return df_new
    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        return pd.DataFrame()

def update_dataset():
    # 1. Load Existing Data
    if os.path.exists(DATA_FILE):
        print(f"📂 Loading existing {DATA_FILE}...")
        df_old = pd.read_csv(DATA_FILE)
        df_old['Date'] = pd.to_datetime(df_old['Date'])
    else:
        df_old = pd.DataFrame()

    # 2. Download New Data
    df_new = download_latest_data()
    
    if df_new.empty:
        print("⚠️ No new data downloaded. Aborting update.")
        return

    # 3. Merge and Deduplicate
    print("🔄 Merging datasets...")
    # Standardize columns for merge
    cols_to_keep = ['Div','Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR','HS','AS','HST','AST','HF','AF','HC','AC','HY','AY','HR','AR']
    # Filter only columns that exist in new data
    cols_new = [c for c in cols_to_keep if c in df_new.columns]
    df_new_clean = df_new[cols_new].copy()
    
    # Concatenate
    if not df_old.empty:
        # Align columns
        df_combined = pd.concat([df_old, df_new_clean], ignore_index=True)
    else:
        df_combined = df_new_clean
        
    # Remove duplicates based on Match Identifier (Date + Teams)
    # We keep the LAST occurrence (assuming new data is more accurate)
    df_combined = df_combined.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='last').sort_values('Date')
    
    print(f"📊 Total Matches after merge: {len(df_combined)}")

    # 4. Run Feature Engineering (Recalculate Elo, Streaks, etc.)
    print("⚙️ Running Feature Engineering Pipeline (v3.0)...")
    df_final = generate_features(df_combined)
    
    # 5. Save
    print(f"💾 Saving to {DATA_FILE}...")
    df_final.to_csv(DATA_FILE, index=False)
    print("✅ Database updated successfully.")
    # --------------------------------------------------------------------------
    # 4. Run Scraper for Live Odds (Real scraping via Puppeteer + Python Processor)
    # --------------------------------------------------------------------------
    print("\n[4/4] Fetching Live Odds from Winamax...")
    try:
        # Step 1: Dump state via Node Puppeteer
        print("   -> Launching Puppeteer Scraper (Step 1: Extract)...")
        # Run node script with shell=True to find node in path easily
        scrape_script = os.path.join(BASE_DIR, "src", "scraper_winamax.js")
        subprocess.run(["node", scrape_script], check=True, shell=True, cwd=BASE_DIR)
        
        # Step 2: Process state via Python
        print("   -> Processing extracted state (Step 2: Parse)...")
        process_script = os.path.join(BASE_DIR, "src", "process_state.py")
        subprocess.run([sys.executable, process_script], check=True, shell=True, cwd=BASE_DIR)
        
        print("   -> Live odds updated successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running scraper pipeline: {e}")
        # We continue even if scraping fails, using old or empty live odds
    except Exception as e:
        print(f"❌ Unexpected error in scraping: {e}")

    print("\n✅ Update Process Completed Successfully!")

if __name__ == "__main__":
    update_dataset()
