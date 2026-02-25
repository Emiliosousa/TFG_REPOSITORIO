import re

with open("app_premier.py", "r", encoding="utf-8") as f:
    content = f.read()

features_func = """
def get_features_from_model(model):
    if hasattr(model, 'feature_names_in_'):
        return list(model.feature_names_in_)
    return MODEL_FEATURES
"""

if "def get_features_from_model" not in content:
    content = content.replace("# --- UTILS ---", "# --- UTILS ---\n" + features_func)

with open("app_premier.py", "w", encoding="utf-8") as f:
    f.write(content)
