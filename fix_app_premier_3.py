import re

with open("app_premier.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix unpack issue
content = content.replace("ph, pd_prob, pa, X_row = probs_data", "ph, pd_prob, pa = probs_data[:3]; X_row = probs_data[3] if len(probs_data) > 3 else {}")

if "return float(proba[2]), float(proba[1]), float(proba[0]), row" not in content:
   content = content.replace("return float(proba[2]), float(proba[1]), float(proba[0])  # H, D, A", "return float(proba[2]), float(proba[1]), float(proba[0]), row")

with open("app_premier.py", "w", encoding="utf-8") as f:
    f.write(content)
