import sys
with open('test_optuna.py', 'r', encoding='utf-8') as f:
    text = f.read()

# remove matplotlib parts at the end
text = text.split("plt.figure(figsize=(10, 6))")[0]

text = "from sklearn.metrics import log_loss, accuracy_score, confusion_matrix\nimport joblib\nimport os\n" + text

with open('test_optuna.py', 'w', encoding='utf-8') as f:
    f.write(text)
