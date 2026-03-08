import pandas as pd
import requests
import io
import os
import sys
import json
import subprocess
from datetime import datetime

# Add src to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

DATA_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'df_final_clean.csv')
ODDS_FILE = os.path.join(BASE_DIR, 'data', 'live_odds.json')
URL_LATEST = "https://www.football-data.co.uk/mmz4281/2526/D1.csv"  # Bundesliga


def download_latest_data():
    print(f"Downloading latest data from {URL_LATEST}...")
    try:
        s = requests.get(URL_LATEST, timeout=15).content
        df_new = pd.read_csv(io.StringIO(s.decode('utf-8')))
        df_new = df_new.dropna(subset=['Date', 'HomeTeam', 'AwayTeam'])
        df_new['Date'] = pd.to_datetime(df_new['Date'], dayfirst=True, errors='coerce')
        return df_new
    except Exception as e:
        print(f"Error downloading data: {e}")
        return pd.DataFrame()


# Team name mapping (football-data.co.uk -> internal CSV names)
TEAM_MAPPING = {
    'Bayern Munich': 'Bayern Munich',
    'Dortmund': 'Borussia Dortmund', 'Borussia Dortmund': 'Borussia Dortmund',
    'RB Leipzig': 'RB Leipzig',
    'Leverkusen': 'Bayer Leverkusen', 'Bayer Leverkusen': 'Bayer Leverkusen',
    'Ein Frankfurt': 'Ein Frankfurt', 'Eintracht Frankfurt': 'Ein Frankfurt',
    'Stuttgart': 'VfB Stuttgart', 'VfB Stuttgart': 'VfB Stuttgart',
    'Freiburg': 'SC Freiburg', 'SC Freiburg': 'SC Freiburg',
    'Wolfsburg': 'VfL Wolfsburg', 'VfL Wolfsburg': 'VfL Wolfsburg',
    "M'gladbach": 'Borussia Monchengladbach', 'Monchengladbach': 'Borussia Monchengladbach',
    'Mainz': 'FSV Mainz 05', 'Mainz 05': 'FSV Mainz 05', 'FSV Mainz 05': 'FSV Mainz 05',
    'Hoffenheim': 'TSG Hoffenheim', 'TSG Hoffenheim': 'TSG Hoffenheim',
    'Augsburg': 'FC Augsburg', 'FC Augsburg': 'FC Augsburg',
    'Werder Bremen': 'Werder Bremen',
    'Union Berlin': 'Union Berlin',
    'Bochum': 'VfL Bochum', 'VfL Bochum': 'VfL Bochum',
    'Heidenheim': '1. FC Heidenheim', '1. FC Heidenheim': '1. FC Heidenheim',
    'Darmstadt': 'SV Darmstadt 98', 'SV Darmstadt 98': 'SV Darmstadt 98',
    'FC Koln': 'FC Cologne', 'Koln': 'FC Cologne', 'FC Cologne': 'FC Cologne',
    'Hertha': 'Hertha BSC', 'Hertha BSC': 'Hertha BSC',
    'Schalke 04': 'FC Schalke 04', 'FC Schalke 04': 'FC Schalke 04',
    'Hannover': 'Hannover 96', 'Hannover 96': 'Hannover 96',
    'Dusseldorf': 'Fortuna Dusseldorf', 'Fortuna Dusseldorf': 'Fortuna Dusseldorf',
    'Holstein Kiel': 'Holstein Kiel',
    'St Pauli': 'FC St. Pauli', 'FC St. Pauli': 'FC St. Pauli',
    'Greuther Furth': 'Greuther Furth',
    'Paderborn': 'SC Paderborn 07', 'SC Paderborn 07': 'SC Paderborn 07',
    'Bielefeld': 'Arminia Bielefeld', 'Arminia Bielefeld': 'Arminia Bielefeld',
    'Nurnberg': 'FC Nurnberg', 'FC Nurnberg': 'FC Nurnberg',
}


def normalize_name(name):
    if not isinstance(name, str):
        return name
    return TEAM_MAPPING.get(name.strip(), name.strip())


def update_dataset():
    """Update dataset with latest Bundesliga data and live odds."""

    # 1. Load existing processed data
    if os.path.exists(DATA_FILE):
        print(f"Loading existing {DATA_FILE}...")
        df_old = pd.read_csv(DATA_FILE)
        df_old['Date'] = pd.to_datetime(df_old['Date'], errors='coerce')
        print(f"   -> {len(df_old)} existing matches loaded.")
    else:
        print(f"Warning: {DATA_FILE} not found. Cannot update CSV data.")
        df_old = None

    # 2. Download new data
    df_new = download_latest_data()

    if not df_new.empty and df_old is not None:
        print(f"Downloaded {len(df_new)} matches from current season.")
        # Normalize names
        df_new['HomeTeam'] = df_new['HomeTeam'].apply(normalize_name)
        df_new['AwayTeam'] = df_new['AwayTeam'].apply(normalize_name)

        # Note: For a full pipeline like LaLiga, we'd need feature_engineering.
        # For now, we just log a reminder.
        print("Note: Full feature re-engineering requires running the notebook pipeline.")
        print("Current update focuses on live odds scraping.")
    elif df_new.empty:
        print("No new CSV data downloaded. Skipping data merge.")

    # 3. Run Scraper for Live Odds
    print("\n[Live Odds] Fetching from Winamax...")
    try:
        # Step 1: Dump state via Node Puppeteer
        print("   -> Launching Puppeteer Scraper (Step 1: Extract)...")
        scrape_script = os.path.join(BASE_DIR, "src", "scraper_winamax.js")
        subprocess.run(["node", scrape_script], check=True, shell=True, cwd=BASE_DIR)

        # Step 2: Process state via Python
        print("   -> Processing extracted state (Step 2: Parse)...")
        process_script = os.path.join(BASE_DIR, "src", "process_state.py")
        subprocess.run([sys.executable, process_script], check=True, shell=True, cwd=BASE_DIR)

        print("   -> Live odds updated successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error running scraper pipeline: {e}")
    except Exception as e:
        print(f"Unexpected error in scraping: {e}")

    print("\nUpdate Process Completed!")


if __name__ == "__main__":
    update_dataset()
