import json

TM_PATH = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\data\transfermarkt_history.json"

def check_tm():
    try:
        with open(TM_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print("Searching 'Alav' in Transfermarkt JSON...")
        found = False
        for s in data:
            for t in data[s]:
                if "Alav" in t['team'] or "laves" in t['team']:
                    print(f"FOUND: {t['team']} in Season {s}")
                    found = True
        
        if not found:
            print("❌ Alaves NOT FOUND in Transfermarkt JSON either.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tm()
