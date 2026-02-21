import json

SOFIFA_PATH = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\data\sofifa_history.json"
OUTPUT_FILE = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\notebooks\teams_list.txt"

def list_teams():
    with open(SOFIFA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        seasons = ["2017", "2024"]
        for s in seasons:
            if s in data:
                out.write(f"\n--- SEASON {s} ---\n")
                teams = sorted([t['team'] for t in data[s]])
                for t in teams:
                    out.write(f"{t}\n")
            else:
                out.write(f"\n--- SEASON {s} NOT FOUND ---\n")

if __name__ == "__main__":
    list_teams()
