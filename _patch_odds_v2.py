"""
Patch notebooks to fix:
1. NB01: Export B365 odds columns to df_final_app.csv so NB02 backtest works.
   Target variable: final_cols
2. NB03: Fix input file path to point to ../df_final_app.csv (Re-applying just in case)
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
        if "final_cols = [" in src and "df_export" in src:
            if "'B365H'" not in src:
                # Replace the last known feature with itself + odds
                new_src = src.replace(
                    "'Away_Dominance_Avg_L5'", 
                    "'Away_Dominance_Avg_L5', 'B365H', 'B365D', 'B365A'"
                )
                
                # Careful with newlines. Let's reconstruct source lines.
                cell["source"] = [s + "\n" if not s.endswith("\n") else s for s in new_src.splitlines()]
                # remove potentially double added newlines if splitlines behavior varies
                # normalized check:
                cell["source"] = [s if s.endswith("\n") else s+"\n" for s in cell["source"]]
                # Remove empty last line if it was created artifactually
                if cell["source"][-1].strip() == "":
                    cell["source"].pop()

                print("Patched NB01: Added B365 odds to final_cols.")
            else:
                print("NB01 already has B365 odds in final_cols.")
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
            lines = new_src.split("\n")
            cell["source"] = [l + "\n" for l in lines[:-1]] + [lines[-1]]
            print("Patched NB03 input file path.")
            break
        elif "INPUT_FILE = '../df_final_app.csv'" in src:
             print("NB03 path already patched.")
             break

with open(nb03_path, "w", encoding="utf-8") as f:
    json.dump(nb03, f, ensure_ascii=False, indent=1)

print("Patching V2 complete.")
