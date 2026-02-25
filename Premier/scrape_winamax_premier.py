import requests
import json
import re
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'data', 'live_odds.json')

def main():
    print("="*60)
    print("WINAMAX PREMIER LEAGUE SCRAPER (Fast API Mode)")
    print("="*60)
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    print("Fetching PL odds from Winamax...")
    try:
        response = requests.get('https://www.winamax.es/apuestas-deportivas/sports/1/79/1', headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"Failed to fetch PL page: {e}")
        return
        
    match = re.search(r'window\.PRELOADED_STATE = (\{.*?\});</script>', html)
    if not match:
        print("Failed to find PRELOADED_STATE in page HTML.")
        return
        
    state = json.loads(match.group(1))
    matches = state.get('matches', {})
    bets = state.get('bets', {})
    odds = state.get('odds', {})
    
    results = []
    for mid, m in matches.items():
        if not isinstance(m, dict): continue
        if m.get('status') != 'PREMATCH': continue
        if m.get('tournamentId') != 1: continue # 1 is Premier League
        
        main_bet_id = m.get('mainBetId')
        if not main_bet_id: continue
            
        bet = bets.get(str(main_bet_id))
        if not bet: continue
            
        outcomes = bet.get('outcomes')
        if not outcomes or len(outcomes) != 3: continue
            
        odd1 = odds.get(str(outcomes[0]))
        oddX = odds.get(str(outcomes[1]))
        odd2 = odds.get(str(outcomes[2]))
        
        if not odd1 or not oddX or not odd2: continue
            
        results.append({
            "home": m.get('competitor1Name'),
            "away": m.get('competitor2Name'),
            "1": odd1,
            "X": oddX,
            "2": odd2,
            "date": m.get('matchStart'),
            "source": "winamax_real"
        })
        print(f"Match: {m.get('competitor1Name')} vs {m.get('competitor2Name')} -> {odd1}/{oddX}/{odd2} (winamax_real)")
        
    if results:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        # sort by date
        results.sort(key=lambda x: x['date'] if x.get('date') else 0)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        print(f"\nSuccessfully extracted {len(results)} Premier League matches.")
        print(f"Saved to {OUTPUT_FILE}")
    else:
        print("No Premier League matches found. Check if tournamentId has changed.")

if __name__ == "__main__":
    main()
