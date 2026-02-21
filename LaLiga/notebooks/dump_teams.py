import json

SOFIFA_PATH = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\data\sofifa_history.json"

def dump_teams():
    with open(SOFIFA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    seasons = ["2017", "2024"] # Check specific seasons Alaves was present
    for s in seasons:
        if s in data:
            print(f"--- Season {s} Teams ---")
            for t in data[s]:
                print(t['team'])
        else:
            print(f"Season {s} not found in JSON.")

if __name__ == "__main__":
    dump_teams()
