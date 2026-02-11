"""
Winamax Premier League Odds Scraper (Deep Mode)
1. Discover matches on PL page.
2. Navigate to EACH match page to extract real odds (bypassing main page missing data).
"""
import json
import os
import sys
import time
import random

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'data', 'live_odds.json')

PL_URL = 'https://www.winamax.es/apuestas-deportivas/sports/1/1/1'

def get_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager

    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_experimental_option('excludeSwitches', ['enable-automation'])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    
    # Anti-detection
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined}); window.chrome = {runtime: {}};"
    })
    return driver

def scrape_match_odds(driver, match_id, match_url):
    """Navigate to match page and extract 1X2 odds."""
    print(f"  Navigating to match {match_id}...")
    driver.get(f"https://www.winamax.es/apuestas-deportivas/match/{match_id}")
    time.sleep(4 + random.random() * 2) # Random wait
    
    state = driver.execute_script("return window.PRELOADED_STATE || null;")
    if not state:
        return None
        
    matches = state.get('matches', {})
    bets = state.get('bets', {})
    outcomes = state.get('outcomes', {})
    
    # Find the match object
    match = matches.get(str(match_id))
    if not match:
        # Maybe key is int
        match = matches.get(int(match_id))
    
    if not match:
        return None
        
    mbid = match.get('mainBetId')
    if not mbid:
        return None
        
    bet = bets.get(str(mbid))
    if not bet:
        return None
        
    odds_vals = {}
    for oid in bet.get('outcomes', []):
        o = outcomes.get(str(oid), {})
        label = o.get('label', '?')
        val = o.get('odds')
        if val:
            odds_vals[label] = val / 100.0
            
    return odds_vals


PL_TEAMS = [
    'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton', 'Burnley', 'Chelsea', 
    'Crystal Palace', 'Everton', 'Fulham', 'Liverpool', 'Luton', 'Man City', 'Man Utd', 
    'Manchester City', 'Manchester United', 'Newcastle', 'Nottm Forest', 'Nottingham Forest',
    'Sheffield Utd', 'Sheffield United', 'Tottenham', 'West Ham', 'Wolves', 'Wolverhampton'
]

def generate_odds(home, away):
    """Generate realistic odds based on team strength tiers."""
    strong = ['Man City', 'Arsenal', 'Liverpool', 'Man Utd', 'Chelsea', 'Tottenham', 'Newcastle']
    h_score = 3 if home in strong else 1
    a_score = 3 if away in strong else 1
    h_score += 0.5 # Home adv
    
    diff = h_score - a_score
    if diff > 1.0: o1, ox, o2 = 1.45, 4.50, 7.00
    elif diff > 0: o1, ox, o2 = 2.10, 3.40, 3.60
    elif diff > -1.0: o1, ox, o2 = 3.60, 3.40, 2.10
    else: o1, ox, o2 = 7.00, 4.50, 1.45
    
    o1 = round(o1 * random.uniform(0.9, 1.1), 2)
    ox = round(ox * random.uniform(0.9, 1.1), 2)
    o2 = round(o2 * random.uniform(0.9, 1.1), 2)
    return f"{o1:.2f}", f"{ox:.2f}", f"{o2:.2f}"

def main():
    print("="*60)
    print("WINAMAX ROBUST SCRAPER (Hybrid)")
    print("="*60)
    
    driver = get_driver()
    all_odds = []
    
    try:
        # Step 1: Get match list
        print(f"Loading {PL_URL}...")
        driver.get(PL_URL)
        time.sleep(8)
        
        state = driver.execute_script("return window.PRELOADED_STATE || null;")
        if not state:
            print("Failed to load PL page.")
            return
            
        matches = state.get('matches', {})
        print(f"Found {len(matches)} matches on listing page.")
        
        # Filter for PL matches
        pl_matches = []
        for mid, m in matches.items():
            if not isinstance(m, dict): continue
            c1 = m.get('competitor1Name')
            c2 = m.get('competitor2Name')
            title = m.get('title', '')
            if not c1 and ' - ' in title:
                parts = title.split(' - ', 1)
                c1, c2 = parts[0].strip(), parts[1].strip()
                
            if c1 and c2:
                # Filter strict PL
                is_pl = any(t in c1 for t in PL_TEAMS) and any(t in c2 for t in PL_TEAMS)
                if is_pl:
                    pl_matches.append({'id': mid, 'home': c1, 'away': c2})
                
        print(f"Identified {len(pl_matches)} valid matches (filtered for PL).")
        
        # Step 2: Visit each match
        for m in pl_matches:
            try:
                odds = scrape_match_odds(driver, m['id'], "")
                if odds:
                    o1 = odds.get('1', odds.get(m['home']))
                    ox = odds.get('X', odds.get('N', odds.get('Empate')))
                    o2 = odds.get('2', odds.get(m['away']))
                    
                    if o1 and ox and o2:
                        entry = {
                            'home': m['home'], 'away': m['away'],
                            '1': f"{o1:.2f}", 'X': f"{ox:.2f}", '2': f"{o2:.2f}",
                            'source': 'winamax_real'
                        }
                    else:
                        # Fallback
                        o1, ox, o2 = generate_odds(m['home'], m['away'])
                        entry = {
                            'home': m['home'], 'away': m['away'],
                            '1': o1, 'X': ox, '2': o2,
                            'source': 'winamax_simulated'
                        }
                else:
                    # Fallback
                    o1, ox, o2 = generate_odds(m['home'], m['away'])
                    entry = {
                        'home': m['home'], 'away': m['away'],
                        '1': o1, 'X': ox, '2': o2,
                        'source': 'winamax_simulated'
                    }
                
                print(f"    Match: {m['home']} vs {m['away']} -> {entry['1']}/{entry['X']}/{entry['2']} ({entry['source']})")
                all_odds.append(entry)
                
            except Exception as e:
                print(f"    Error scraping {m['id']}: {e}")

        # Save
        if all_odds:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_odds, f, indent=2, ensure_ascii=False)
            print(f"\nSaved {len(all_odds)} matches to {OUTPUT_FILE}")
        else:
            print("No odds extracted.")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
