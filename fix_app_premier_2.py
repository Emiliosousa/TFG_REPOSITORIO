import re

with open("app_premier.py", "r", encoding="utf-8") as f:
    content = f.read()

funcs = """
import unicodedata

def normalize_text_safe(text):
    if not isinstance(text, str): return ""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
"""

if "def normalize_text_safe" not in content:
    content = content.replace("# --- UTILS ---", "# --- UTILS ---\n" + funcs)

with open("app_premier.py", "w", encoding="utf-8") as f:
    f.write(content)
