import json
import os
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, '..', 'state_dump.json')
OUTPUT_FILE = os.path.join(BASE_DIR, '..', 'data', 'live_odds.json')

def extract_matches(data, tournament_id=None):
    results = []
    
    matches = data.get('matches', {})
    bets = data.get('bets', {})
    odds = data.get('odds', {})
    
    print(f"Total Matches in dump: {len(matches)}")
    debug_limit = 10
    
    for mid, match in matches.items():
        if not isinstance(match, dict):
            continue
            
        # Status 'PREMATCH'
        if match.get('status') != 'PREMATCH':
            continue
            
        # Tournament filter (Premier League is typically 1 on Winamax but might change. Let's filter by tournamentId if passed or just by string if we can.
        if tournament_id is not None:
            if match.get('tournamentId') != tournament_id:
                continue
        
        # Main Bet Validity
        main_bet_id = match.get('mainBetId')
        if not main_bet_id:
            continue
            
        # Bet Lookup (keys are strings in JSON)
        bet = bets.get(str(main_bet_id))
        if not bet:
            continue
            
        outcomes = bet.get('outcomes')
        if not outcomes or len(outcomes) != 3:
            continue
            
        # Odds Lookup
        odd1 = odds.get(str(outcomes[0]))
        oddX = odds.get(str(outcomes[1]))
        odd2 = odds.get(str(outcomes[2]))
        
        if not odd1 or not oddX or not odd2:
            continue
            
        # Add to results
        results.append({
            "home": match.get('competitor1Name'),
            "away": match.get('competitor2Name'),
            "1": odd1,
            "X": oddX,
            "2": odd2,
            "date": match.get('matchStart'),
            "tournament": match.get('tournamentId')
        })
        
    return results

def main():
    if not os.path.exists(STATE_FILE):
        print(f"Error: State file not found at {STATE_FILE}")
        sys.exit(1)
        
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print("Loaded state dump.")
        
        # Attempt 1: Premier League (ID 1)
        print("Attempting to extract Premier League matches (TD 1)...")
        matches = extract_matches(data, tournament_id=1)
        
        if not matches:
            print("No Premier League matches found for tournament ID 1. Trying to search by name...")
            tourns = data.get('tournaments', {})
            pl_id = None
            for tid, t in tourns.items():
                if 'Premier League' in t.get('name', ''):
                    pl_id = int(tid)
                    break
            
            if pl_id:
                print(f"Found Premier League under ID {pl_id}. Extracting...")
                matches = extract_matches(data, tournament_id=pl_id)
            else:
                print("Could not find Premier League tournament ID. Falling back to ALL PREMATCH matches.")
                matches = extract_matches(data, tournament_id=None)
            
        # Sort by date
        matches.sort(key=lambda x: x['date'])
        
        # Limit to 10 - NO, WE WANT ALL PREMIER LEAGUE MATCHES
        
        print(f"Found {len(matches)} matches.")
        
        # Save
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=2)
            
        print(f"Saved to {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"Error processing state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
