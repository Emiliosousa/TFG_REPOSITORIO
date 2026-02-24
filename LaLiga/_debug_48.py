import json

path = 'LaLiga/notebooks/02_Modelado_Avanzado_Academic_v2.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")

for i, cell in enumerate(nb['cells']):
    # Check index or execution count
    if i == 48 or cell.get('execution_count') == 48:
        print(f"\n--- CELL Index: {i} | Execution Count: {cell.get('execution_count')} ---")
        print("".join(cell.get('source', [])))
        print("-" * 40)
    
    # Also look for the fit() call which was failing earlier in what user called "cell 8" (index 12)
    # in case cell numbers shifted.
    src = "".join(cell.get('source', []))
    if 'final_model.fit' in src:
        print(f"\n--- POTENTIAL Target (fit call) at Cell Index: {i} | Count: {cell.get('execution_count')} ---")
        print(src)
        print("-" * 40)
