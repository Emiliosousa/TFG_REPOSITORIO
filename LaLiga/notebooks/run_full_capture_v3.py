import subprocess
import sys
import os

def run():
    # Set environment variable for Python IO encoding
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    # Run the validation script
    result = subprocess.run(
        [sys.executable, 'run_validation_2025_headless.py'], 
        capture_output=True, 
        env=env
    )
    
    # Manually decode with error replacement
    stdout = result.stdout.decode('utf-8', errors='replace')
    stderr = result.stderr.decode('utf-8', errors='replace')
    
    print(stdout)
    if stderr:
        print("ERRORS:")
        print(stderr)

if __name__ == '__main__':
    run()
