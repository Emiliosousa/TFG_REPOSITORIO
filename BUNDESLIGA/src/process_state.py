import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, '..', 'state_dump.json')
OUTPUT_FILE = os.path.join(BASE_DIR, '..', 'data', 'live_odds.json')

# Bundesliga 1 team name fragments - must match BOTH competitors
BL1_TEAMS = [
    'Bayern', 'Borussia Dortmund', 'Leipzig', 'Leverkusen',
    'Frankfurt', 'Stuttgart', 'Freiburg', 'Wolfsburg',
    'Hoffenheim', 'Augsburg', 'Werder Bremen', 'Union Berlin',
    'Bochum', 'Heidenheim', 'Holstein Kiel', 'St. Pauli',
    'Mainz 05', 'Gladbach', 'Mainz',
]


def is_bl1_team(name):
    """Check if a team name matches a known Bundesliga 1 team."""
    for frag in BL1_TEAMS:
        if frag in name:
            return True
    return False


def extract_bl1_matches(data):
    """Extract only Bundesliga 1 matches (both teams must be BL1 teams)."""
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

        c1 = str(match.get('competitor1Name', ''))
        c2 = str(match.get('competitor2Name', ''))

        # Both teams must be from Bundesliga 1
        if not (is_bl1_team(c1) and is_bl1_team(c2)):
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

        # Extract Bundesliga 1 matches
        print("Extracting Bundesliga 1 matches...")
        matches = extract_bl1_matches(data)

        # Filter out matches without a valid date
        matches = [m for m in matches if m.get('date', 0) > 0]
        # Sort by date
        matches.sort(key=lambda x: x.get('date', 0))

        # Keep only next matches (up to ~2 matchdays, 14 days window)
        if matches:
            first_date = matches[0].get('date', 0)
            matches = [m for m in matches if m.get('date', 0) - first_date <= 14 * 86400][:18]

        print(f"Found {len(matches)} Bundesliga 1 matches.")
        for m in matches:
            print(f"  {m['home']} vs {m['away']} @ {m['1']}/{m['X']}/{m['2']}")

        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=2, ensure_ascii=False)
        print(f"Saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error processing state: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
