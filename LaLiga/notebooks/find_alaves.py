import json
import difflib

SOFIFA_PATH = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\data\sofifa_history.json"

def find_team():
    with open(SOFIFA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print("Searching for 'Alav' or 'Deportivo' in team names...")
    
    found_teams = set()
    for season, teams in data.items():
        for t in teams:
            name = t['team']
            if "Alav" in name or "Depor" in name:
                found_teams.add(name)
                
    print("\nFound Candidates:")
    for team in sorted(found_teams):
        print(f" - {team}")

if __name__ == "__main__":
    find_team()
