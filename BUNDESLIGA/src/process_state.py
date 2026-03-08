import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, '..', 'state_dump.json')
OUTPUT_FILE = os.path.join(BASE_DIR, '..', 'data', 'live_odds.json')

def extract_matches(data, tournament_id=None):
    results = []
    matches = data.get('matches', {})
    bets = data.get('bets', {})
    odds = data.get('odds', {})

    print(f"Total matches in dump: {len(matches)}")

    for mid, match in matches.items():
        if not isinstance(match, dict):
            continue
        if match.get('status') != 'PREMATCH':
            continue
        if tournament_id is not None:
            if match.get('tournamentId') != tournament_id:
                continue

        main_bet_id = match.get('mainBetId')
        if not main_bet_id:
            continue
        bet = bets.get(str(main_bet_id))
        if not bet:
            continue
        outcomes = bet.get('outcomes')
        if not outcomes or len(outcomes) != 3:
            continue

        odd1 = odds.get(str(outcomes[0]))
        oddX = odds.get(str(outcomes[1]))
        odd2 = odds.get(str(outcomes[2]))
        if not odd1 or not oddX or not odd2:
            continue

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

        # Attempt: Bundesliga
        print("Extracting Bundesliga matches...")
        matches = extract_matches(data, tournament_id=None)

        # Filter to only Bundesliga-like tournaments by searching tournament names
        if not matches:
            tourns = data.get('tournaments', {})
            bl_id = None
            for tid, t in tourns.items():
                name = t.get('name', '')
                if 'Bundesliga' in name and '2' not in name:
                    bl_id = int(tid)
                    break
            if bl_id:
                print(f"Found Bundesliga under ID {bl_id}.")
                matches = extract_matches(data, tournament_id=bl_id)

        matches.sort(key=lambda x: x.get('date', 0))
        print(f"Found {len(matches)} matches.")

        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=2)
        print(f"Saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error processing state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
