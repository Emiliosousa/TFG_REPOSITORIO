import json
import os
import re

source_dir = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\notebooks"
target_dir = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\Premier\notebooks"

notebooks_to_convert = [
    "01_Ingenieria_de_Datos_Academic_v2.ipynb",
    "02_Modelado_Avanzado_Academic_v2.ipynb",
    "03_auditoria_y_finanzas.ipynb"
]

def process_text(text):
    text = text.replace("LaLiga", "Premier")
    text = text.replace("laliga", "premier")
    text = text.replace("LALIGA", "PREMIER")
    text = text.replace("SP1", "E0")
    text = text.replace("sp1", "e0")
    text = text.replace("df_laliga", "df_premier")
    return text

pl_mapping = """TEAM_MAPPING = {
    'Man United': 'Manchester United', 'Man City': 'Manchester City',
    'Spurs': 'Tottenham', 'Newcastle': 'Newcastle United',
    'Leicester': 'Leicester City', 'Norwich': 'Norwich City',
    'Leeds': 'Leeds United', 'Sheffield United': 'Sheffield Utd',
    'West Ham': 'West Ham United', 'Wolves': 'Wolverhampton',
    'Brighton': 'Brighton', 'Huddersfield': 'Huddersfield',
    'Cardiff': 'Cardiff City', 'Swansea': 'Swansea City',
    'Stoke': 'Stoke City', 'Hull': 'Hull City',
    'QPR': 'QPR', 'West Brom': 'West Brom',
    'Bournemouth': 'Bournemouth', "Nott'm Forest": 'Nott. Forest',
    'Luton': 'Luton', 'Ipswich': 'Ipswich',
}"""

for nb_name in notebooks_to_convert:
    src_path = os.path.join(source_dir, nb_name)
    dst_path = os.path.join(target_dir, nb_name)
    
    if os.path.exists(src_path):
        with open(src_path, 'r', encoding='utf-8') as f:
            nb_data = json.load(f)
            
        for cell in nb_data.get('cells', []):
            if 'source' in cell:
                # Need to find the assignment of TEAM_MAPPING inside cell['source']
                # since cell['source'] is a list of lines, we process lines
                new_source = []
                inside_mapping = False
                for line in cell['source']:
                    if line.startswith('TEAM_MAPPING = {'):
                        inside_mapping = True
                        new_source.append(pl_mapping + '\n')
                    elif inside_mapping:
                        if '}' in line and not line.strip().startswith("'"):
                            # This is likely the end of the mapping dictionary
                            inside_mapping = False
                    else:
                        new_source.append(process_text(line))
                cell['source'] = new_source
                
        with open(dst_path, 'w', encoding='utf-8') as f:
            json.dump(nb_data, f, indent=1, ensure_ascii=False)
        print(f"Converted {nb_name} -> {dst_path}")
    else:
        print(f"NOT FOUND: {src_path}")
