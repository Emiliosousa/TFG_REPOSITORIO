import subprocess

# Run the notebook process and catch its exact error traceback regarding the empty Optuna result 
result = subprocess.run(['python', r'.\notebooks\02_Modelado_Avanzado_v3_Bundesliga.py'], capture_output=True, text=True)
print("--- STDOUT ---")
print(result.stdout)
print("--- STDERR ---")
print(result.stderr)
