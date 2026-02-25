import json
import os

target_dir = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\Premier\notebooks"

# Update 01...ipynb filename pattern
nb01 = os.path.join(target_dir, "01_Ingenieria_de_Datos_Academic_v2.ipynb")
with open(nb01, 'r', encoding='utf-8') as f:
    data = json.load(f)

for cell in data.get('cells', []):
    if 'source' in cell:
        for i, line in enumerate(cell['source']):
            if 'filename = f"E0_{season_str}.csv"' in line or 'filename = f"E0_{season_str}.csv"' in line:
                cell['source'][i] = line.replace('f"E0_{season_str}.csv"', 'f"E0-20{year:02d}-{(year+1)%100:02d}.csv"')
            # In case season_str is not used properly now, just use the string literal above directly
            elif 'season_str = ' in line:
                cell['source'][i] = line.replace('season_str = f"{year:02d}{(year+1)%100:02d}"', 'pass')

                
with open(nb01, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=1, ensure_ascii=False)

print("Updated 01.")
