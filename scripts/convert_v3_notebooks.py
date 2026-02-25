import json
import os
import re

source_dir = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\notebooks"
target_dir = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\Premier\notebooks"

notebooks_to_convert = [
    "01_Ingenieria_de_Datos_v3.ipynb",
    "02_Modelado_Avanzado_v3.ipynb",
]

def process_text(text):
    text = text.replace("LaLiga", "Premier")
    text = text.replace("laliga", "premier")
    text = text.replace("LALIGA", "PREMIER")
    text = text.replace("SP1", "E0")
    text = text.replace("sp1", "e0")
    text = text.replace("df_laliga", "df_premier")
    return text

for nb_name in notebooks_to_convert:
    src_path = os.path.join(source_dir, nb_name)
    dst_path = os.path.join(target_dir, nb_name)
    
    if os.path.exists(src_path):
        with open(src_path, 'r', encoding='utf-8') as f:
            nb_data = json.load(f)
            
        for cell in nb_data.get('cells', []):
            if 'source' in cell:
                new_source = []
                for line in cell['source']:
                    new_source.append(process_text(line))
                cell['source'] = new_source
                
        with open(dst_path, 'w', encoding='utf-8') as f:
            json.dump(nb_data, f, indent=1, ensure_ascii=False)
        print(f"Converted {nb_name} -> {dst_path}")
    else:
        print(f"NOT FOUND: {src_path}")
