import requests
import json
import re

headers = {'User-Agent': 'Mozilla/5.0'}
html = requests.get('https://www.winamax.es/apuestas-deportivas/sports/1/1/1', headers=headers).text
match = re.search(r'window\.PRELOADED_STATE = (\{.*?\});</script>', html)
if match:
    state = json.loads(match.group(1))
    tournaments = state.get('tournaments', {})
    for t_id, t in tournaments.items():
        if 'Premier' in t.get('name', ''):
            print(f"ID: {t_id}, Name: {t.get('name')}, CategoryId: {t.get('categoryId')}")
            
    categories = state.get('categories', {})
    for t_id, t in tournaments.items():
        if 'Premier' in t.get('name', ''):
            c_id = t.get('categoryId')
            if str(c_id) in categories:
                print(f"URL: https://www.winamax.es/apuestas-deportivas/sports/1/{c_id}/{t_id}")
