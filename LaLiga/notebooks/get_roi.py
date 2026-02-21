
import subprocess
import sys
import os

def run():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run([sys.executable, 'run_validation_2025_headless.py'], capture_output=True, env=env)
    output = result.stdout.decode('utf-8', errors='ignore')
    
    # Extract ROI line
    for line in output.split('\n'):
        if "ROI:" in line:
            print(line.strip())
        if "Profit:" in line:
            print(line.strip())

if __name__ == '__main__':
    run()
