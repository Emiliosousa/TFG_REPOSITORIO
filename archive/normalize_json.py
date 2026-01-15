import json
import unicodedata

def remove_accents(input_str):
    if not isinstance(input_str, str): return input_str
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

JSON_FILE = "data/team_logos.json"

def main():
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
        
    new_data = {}
    for k, v in data.items():
        # Normalize Key
        new_key = remove_accents(k)
        # Normalize Value path if it has accents (unlikely but good practice)
        # We leave the URL/Path alone mostly, but the KEY is what matters for lookup
        new_data[new_key] = v
        
    # Manual fixes ensuring consistency if any duplicates merged
    # (e.g. 'Alaves' vs 'Alavés' -> 'Alaves')
    
    with open(JSON_FILE, 'w') as f:
        json.dump(new_data, f, indent=4)
    print(f"Normalized {len(new_data)} keys.")

if __name__ == "__main__":
    main()
