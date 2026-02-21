import subprocess
import sys

def run():
    result = subprocess.run([sys.executable, 'run_validation_2025_headless.py'], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("ERRORS:")
        print(result.stderr)

if __name__ == '__main__':
    run()
