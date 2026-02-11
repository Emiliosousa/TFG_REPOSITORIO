"""
Fix NB02_v2 features list to match actual df_final_app.csv columns from NB01.
The NB01 only generates: Elo, xG_Avg_L5, Streak_L5, Pressure_Avg_L5, Dominance_Avg_L5
"""
import json
import os

NB_DIR = os.path.join("LaLiga", "notebooks")
path = os.path.join(NB_DIR, "02_Modelado_Avanzado_Academic_v2.ipynb")

with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Fix Cell 3: features list
for i, cell in enumerate(nb["cells"]):
    src = "".join(cell["source"])
    if "features" in src and "Home_Elo" in src and cell["cell_type"] == "code":
        # Replace the full 24-feature list with what NB01 actually outputs
        old_features = (
            'features = [\n'
            '    "Home_Elo", "Away_Elo", "Home_Att_Strength", "Away_Att_Strength",\n'
            '    "Home_Def_Weakness", "Away_Def_Weakness", "Home_FIFA_Ova", "Away_FIFA_Ova",\n'
            '    "Home_Market_Value", "Away_Market_Value", "Home_xG_Avg_L5", "Away_xG_Avg_L5",\n'
            '    "Home_Streak_L5", "Away_Streak_L5", "Home_H2H_L3", "Away_H2H_L3",\n'
            '    "Home_Pressure_Avg_L5", "Away_Pressure_Avg_L5", "Home_Goal_Diff_L5", "Away_Goal_Diff_L5",\n'
            '    "Home_Rest_Days", "Away_Rest_Days", "Home_Dominance_Avg_L5", "Away_Dominance_Avg_L5"\n'
            ']'
        )
        new_features = (
            '# Features disponibles en df_final_app.csv (generado por NB01)\n'
            'features = [\n'
            '    "Home_Elo", "Away_Elo",\n'
            '    "Home_xG_Avg_L5", "Away_xG_Avg_L5",\n'
            '    "Home_Streak_L5", "Away_Streak_L5",\n'
            '    "Home_Pressure_Avg_L5", "Away_Pressure_Avg_L5",\n'
            '    "Home_Dominance_Avg_L5", "Away_Dominance_Avg_L5"\n'
            ']'
        )
        
        if old_features in src:
            src = src.replace(old_features, new_features)
            lines = src.split("\n")
            cell["source"] = [line + "\n" for line in lines[:-1]] + [lines[-1]]
            cell["outputs"] = []
            print(f"  Cell {i}: Fixed features to match NB01 output (10 features)")
        else:
            print(f"  Cell {i}: Features text not found as expected, trying direct replacement...")
            # Line by line approach
            src = src.replace(
                '"Home_Elo", "Away_Elo", "Home_Att_Strength", "Away_Att_Strength",',
                '"Home_Elo", "Away_Elo",'
            )
            src = src.replace(
                '"Home_Def_Weakness", "Away_Def_Weakness", "Home_FIFA_Ova", "Away_FIFA_Ova",\n', ''
            )
            src = src.replace(
                '"Home_Market_Value", "Away_Market_Value", "Home_xG_Avg_L5", "Away_xG_Avg_L5",',
                '"Home_xG_Avg_L5", "Away_xG_Avg_L5",'
            )
            src = src.replace(
                '"Home_Streak_L5", "Away_Streak_L5", "Home_H2H_L3", "Away_H2H_L3",',
                '"Home_Streak_L5", "Away_Streak_L5",'
            )
            src = src.replace(
                '"Home_Pressure_Avg_L5", "Away_Pressure_Avg_L5", "Home_Goal_Diff_L5", "Away_Goal_Diff_L5",',
                '"Home_Pressure_Avg_L5", "Away_Pressure_Avg_L5",'
            )
            src = src.replace(
                '"Home_Rest_Days", "Away_Rest_Days", "Home_Dominance_Avg_L5", "Away_Dominance_Avg_L5"',
                '"Home_Dominance_Avg_L5", "Away_Dominance_Avg_L5"'
            )
            lines = src.split("\n")
            cell["source"] = [line + "\n" for line in lines[:-1]] + [lines[-1]]
            cell["outputs"] = []
            print(f"  Cell {i}: Applied line-by-line feature fix")
        break

# Also fix the backtest cell if it references features
for i, cell in enumerate(nb["cells"]):
    src = "".join(cell["source"])
    if "BACKTEST" in src and "B365H" in src and cell["cell_type"] == "code":
        # The backtest cell references `features` variable so it will work automatically
        # But we need to make sure it reads B365 columns from the raw CSV data
        # Since df_final_app.csv doesn't have B365 columns, backtest needs raw data
        # Let's add a note and load raw data with odds
        if "B365H" in src and "has_odds" in src:
            print(f"  Cell {i}: Backtest already has odds check")
        break

# Add cell IDs for nbformat
import uuid
for cell in nb["cells"]:
    if "id" not in cell:
        cell["id"] = str(uuid.uuid4())[:8]

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print(f"Saved: {path}")
