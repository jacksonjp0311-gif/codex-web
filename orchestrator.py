"""
orchestrator.py
Runs the full Codex cycle:
1. Fetch new stones from mirrors into inbox/
2. Run watcher once to validate + append to ledger
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def run_step(module_name: str, label: str):
    """Run a Python module as a subprocess and log outcome."""
    print(f"\n=== {label} ===")
    result = subprocess.run(
        [sys.executable, "-m", module_name],
        cwd=PROJECT_ROOT
    )
    if result.returncode == 0:
        print(f"{label} completed successfully.")
    else:
        print(f"⚠️ {label} failed with code {result.returncode}")
    return result.returncode

def main():
    # Step 1: Fetch new stones
    run_step("codex_fetcher.fetcher", "Fetcher")

    # Step 2: Run watcher once
    run_step("codex_watcher.cli", "Watcher")

if __name__ == "__main__":
    main()
