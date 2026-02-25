import json
import os

target_dir = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\Premier\notebooks"
nb02 = os.path.join(target_dir, "02_Modelado_Avanzado_Academic_v2.ipynb")

with open(nb02, 'r', encoding='utf-8') as f:
    data = json.load(f)

for cell in data.get('cells', []):
    if 'source' in cell:
        for i, line in enumerate(cell['source']):
            if "missing_mask = df[cols_to_check].isnull().any(axis=1)" in line:
                cell['source'][i] = "cols_to_check = [c for c in cols_to_check if c in df.columns]\nif len(cols_to_check) > 0:\n    " + line + "\nelse:\n    missing_mask = pd.Series([False]*len(df))\n"

with open(nb02, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=1, ensure_ascii=False)

print("Fixed Notebook 02 strict checking KeyError.")
