import requests
import json
import re

headers = {'User-Agent': 'Mozilla/5.0'}
html = requests.get('https://www.winamax.es/apuestas-deportivas/sports/1/79/1', headers=headers).text
match = re.search(r'window\.PRELOADED_STATE = (\{.*?\});</script>', html)
if match:
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
            "date": m.get('matchStart')
        })
        print(f"{m.get('competitor1Name')} vs {m.get('competitor2Name')} -> 1: {odd1}, X: {oddX}, 2: {odd2}")
    
    with open('Premier/data/live_odds.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
