import json
import difflib

SOFIFA_PATH = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\data\sofifa_history.json"
OUTPUT_FILE = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\notebooks\alaves_match.txt"

def find_match():
    with open(SOFIFA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    all_teams = set()
    for s in data:
        for t in data[s]:
            all_teams.add(t['team'])
            
    matches = difflib.get_close_matches("Alaves", list(all_teams), n=5, cutoff=0.4)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Matches for 'Alaves':\n")
        for m in matches:
            f.write(f"- {m}\n")
            
        f.write("\nSearching for 'Depor':\n")
        depor_matches = [t for t in all_teams if "Depor" in t]
        for m in sorted(depor_matches):
            f.write(f"- {m}\n")

if __name__ == "__main__":
    find_match()
