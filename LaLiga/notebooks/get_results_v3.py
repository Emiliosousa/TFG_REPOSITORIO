import json

with open('02_Modelado_Avanzado_v3.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb.get('cells', []):
    if cell.get('cell_type') == 'code':
        outputs = cell.get('outputs', [])
        for out in outputs:
            if 'text' in out:
                text_join = "".join(out['text'])
                if 'RESUMEN' in text_join or 'EVALUACIÓN' in text_join or 'Folds' in text_join:
                    print(text_join)
