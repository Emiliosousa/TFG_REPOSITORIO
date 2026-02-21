import json

SOFIFA_PATH = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\data\sofifa_history.json"
OUTPUT_FILE = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\notebooks\all_teams.txt"

def list_all_teams():
    with open(SOFIFA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    all_teams = set()
    for s in data:
        for t in data[s]:
            all_teams.add(t['team'])
            
    sorted_teams = sorted(list(all_teams))
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write(f"Total Unique Teams: {len(sorted_teams)}\n\n")
        for t in sorted_teams:
            out.write(f"{t}\n")
            
        out.write("\n\n--- SEARCH RESULTS FOR 'laves' ---\n")
        for t in sorted_teams:
            if "laves" in t.lower() or "lavés" in t.lower():
                out.write(f"MATCH: {t}\n")

if __name__ == "__main__":
    list_all_teams()
