import nbformat
import os

NOTEBOOK_PATH = r"c:\Users\emili\OneDrive\Escritorio\US SEVILLA\winamax-odds-detector\TFG_REPOSITORIO\LaLiga\notebooks\02_Modelado_Avanzado_Academic_v2.ipynb"

def repatch_position():
    if not os.path.exists(NOTEBOOK_PATH):
        print(f"Notebook not found: {NOTEBOOK_PATH}")
        return

    nb = nbformat.read(NOTEBOOK_PATH, as_version=4)
    
    # 1. Identify critical cells
    load_idx = -1
    cleaning_idx = -1
    split_idx = -1
    
    for i, cell in enumerate(nb.cells):
        source = cell.source
        if "pd.read_csv" in source and "df_final_app.csv" in source:
            load_idx = i
        if "STRICT DATA CLEANING" in source:
            cleaning_idx = i
        if "TimeSeriesSplit" in source or "X =" in source:
            # We want the FIRST occurrence of splitting/defining X
            if split_idx == -1 and "X =" in source:
                 split_idx = i
    
    print(f"Found: Load Cell: {load_idx}, Cleaning Cell: {cleaning_idx}, Split Cell: {split_idx}")
    
    # 2. Logic to Fix
    if cleaning_idx != -1:
        print(f"Removing misplaced cleaning cell at index {cleaning_idx}...")
        popped_cell = nb.cells.pop(cleaning_idx)
        
        # Recalculate indices after pop
        load_idx = -1
        split_idx = -1
        for i, cell in enumerate(nb.cells):
            source = cell.source
            if "pd.read_csv" in source and "df_final_app.csv" in source:
                load_idx = i
            if "TimeSeriesSplit" in source or "X =" in source:
                if split_idx == -1 and "X =" in source:
                     split_idx = i
        
        # 3. Determine new insertion point
        # Ideally: After Load, but Before Split/X definition.
        
        if load_idx != -1:
            # Check if there are cells between load and split (e.g. data viewing)
            # Safe bet: Insert right after Data Load cell.
            insert_pos = load_idx + 1
            print(f"Re-inserting cleaning cell at index {insert_pos} (After Data Load)...")
            nb.cells.insert(insert_pos, popped_cell)
            
            nbformat.write(nb, NOTEBOOK_PATH)
            print("✅ Notebook re-patched successfully!")
        else:
            print("❌ Critical: Could not find Data Loading cell (pd.read_csv). Cannot place patch correctly.")
            # Put it back where it was? No, that breaks.
            # Maybe append?
    else:
        print("Cleaning cell not found. Was it already removed?")

if __name__ == "__main__":
    repatch_position()
