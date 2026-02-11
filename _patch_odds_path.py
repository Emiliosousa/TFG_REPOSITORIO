"""
Patch notebooks to fix:
1. NB01: Export B365 odds columns to df_final_app.csv so NB02 backtest works.
2. NB03: Fix input file path to point to ../df_final_app.csv
"""
import json
import os

NB_DIR = os.path.join("LaLiga", "notebooks")

# --- Patch NB01 ---
nb01_path = os.path.join(NB_DIR, "01_Ingenieria_de_Datos_Academic_v2.ipynb")
with open(nb01_path, "r", encoding="utf-8") as f:
    nb01 = json.load(f)

for cell in nb01["cells"]:
    if cell["cell_type"] == "code":
        src = "".join(cell["source"])
        if "to_csv" in src and "cols_to_export" in src:
            # We found the export cell. Let's ensure B365 columns are included.
            if "'B365H'" not in src:
                # Naive replace: find the list start and insert odds
                # Assuming the list is like: cols_to_export = ['Date', 'Season', ...
                new_src = src.replace("cols_to_export = [", "cols_to_export = ['B365H', 'B365D', 'B365A', ")
                cell["source"] = [s + "\n" if not s.endswith("\n") else s for s in new_src.splitlines()]
                # fix double newlines if any
                cell["source"] = [s for s in cell["source"] if s.strip() != ""] 
                # Add proper newlines back
                cell["source"] = [s if s.endswith("\n") else s+"\n" for s in cell["source"]]
                # Remove last newline if it wasn't there
                if not new_src.endswith("\n") and cell["source"][-1].endswith("\n"):
                     cell["source"][-1] = cell["source"][-1][:-1]
                
                print("Patched NB01 to include B365 odds in export.")
                break

with open(nb01_path, "w", encoding="utf-8") as f:
    json.dump(nb01, f, ensure_ascii=False, indent=1)

# --- Patch NB03 ---
nb03_path = os.path.join(NB_DIR, "03_auditoria_y_finanzas.ipynb")
with open(nb03_path, "r", encoding="utf-8") as f:
    nb03 = json.load(f)

for cell in nb03["cells"]:
    if cell["cell_type"] == "code":
        src = "".join(cell["source"])
        if "INPUT_FILE = 'df_final_app.csv'" in src:
            new_src = src.replace("INPUT_FILE = 'df_final_app.csv'", "INPUT_FILE = '../df_final_app.csv'")
            cell["source"] = [new_src] # usually valid if single block, but strictly should split lines
            # Safer way:
            lines = new_src.split("\n")
            cell["source"] = [l + "\n" for l in lines[:-1]] + [lines[-1]]
            print("Patched NB03 input file path.")
            break

with open(nb03_path, "w", encoding="utf-8") as f:
    json.dump(nb03, f, ensure_ascii=False, indent=1)

print("Patching complete.")
