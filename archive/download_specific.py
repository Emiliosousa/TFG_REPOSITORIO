import os
import json
import requests

LOGOS_DIR = "data/logos"
JSON_FILE = "data/team_logos.json"

# URLs found by Browser Agent
specific_logos = {
    "Real Madrid": "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Real_Madrid_CF.svg/762px-Real_Madrid_CF.svg.png",
    "RC Celta": "https://upload.wikimedia.org/wikipedia/en/thumb/1/12/RC_Celta_de_Vigo_logo.svg/577px-RC_Celta_de_Vigo_logo.svg.png",
    "Getafe CF": "https://upload.wikimedia.org/wikipedia/commons/b/b9/Getafe_CF_Logo.png",
    "Girona": "https://upload.wikimedia.org/wikipedia/fr/thumb/5/56/Logo_Girona_FC_-_2022.svg/1024px-Logo_Girona_FC_-_2022.svg.png", # Note key change to match CSV likely
    "Real Sociedad": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f1/Real_Sociedad_logo.svg/891px-Real_Sociedad_logo.svg.png",
    # Mapped keys for robust matching
    "Girona FC": "https://upload.wikimedia.org/wikipedia/fr/thumb/5/56/Logo_Girona_FC_-_2022.svg/1024px-Logo_Girona_FC_-_2022.svg.png",
    "Celta de Vigo": "https://upload.wikimedia.org/wikipedia/en/thumb/1/12/RC_Celta_de_Vigo_logo.svg/577px-RC_Celta_de_Vigo_logo.svg.png" 
}

def main():
    if not os.path.exists(LOGOS_DIR):
        os.makedirs(LOGOS_DIR)

    # Load existing map
    local_map = {}
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            try: local_map = json.load(f)
            except: pass

    headers = {'User-Agent': 'Mozilla/5.0'}

    for team, url in specific_logos.items():
        safe_name = team.replace(" ", "_").replace(".", "")
        filename = f"{LOGOS_DIR}/{safe_name}.png"
        
        try:
            print(f"Downloading {team}...")
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(r.content)
                local_map[team] = filename
                print(f"✅ Saved {filename}")
            else:
                print(f"❌ Failed {team}: {r.status_code}")
                # Fallback to URL if download fails again
                local_map[team] = url
        except Exception as e:
            print(f"❌ Error {team}: {e}")
            local_map[team] = url

    # Save
    with open(JSON_FILE, 'w') as f:
        json.dump(local_map, f, indent=4)
    print("Updated team_logos.json")

if __name__ == "__main__":
    main()
