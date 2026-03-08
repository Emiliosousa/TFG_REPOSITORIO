import json
with open('notebooks/02_Modelado_Avanzado_v3_Bundesliga.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'for i in range\((.*?)\):', text)
for m in matches:
    print(m.group(0))
