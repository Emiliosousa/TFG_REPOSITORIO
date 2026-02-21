import subprocess
import sys

def run():
    # Force UTF-8 encoding for subprocess output
    result = subprocess.run(
        [sys.executable, 'run_validation_2025_headless.py'], 
        capture_output=True, 
        encoding='utf-8', 
        errors='replace'
    )
    print(result.stdout)
    if result.stderr:
        print("ERRORS:")
        print(result.stderr)

if __name__ == '__main__':
    run()
