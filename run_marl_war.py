import subprocess
import time
import os
import sys

# Colors for Terminal
RED = "\033[91m"
BLUE = "\033[94m"
GREEN = "\033[92m"
RESET = "\033[0m"


def log(round_num, message, color=RESET):
    print(f"\n{color}⚡ [ROUND {round_num}] {message}{RESET}")


def run_script(script_name):
    """Runs a script and waits for it to finish."""
    try:
        # Using python3 to be safe on Mac
        result = subprocess.run(
            ["python3", script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(result.stdout)  # Print the script's output to the console
        if result.returncode != 0:
            print(f"Error running {script_name}: {result.stderr}")
    except Exception as e:
        print(f"Failed to run {script_name}: {e}")


def start_war():
    # 1. Start Fresh
    log(0, "RESETTING ENVIRONMENT...", RED)
    run_script("reset_demo.py")
    time.sleep(1)

    MAX_ROUNDS = 3

    for round_num in range(1, MAX_ROUNDS + 1):
        log(round_num, "🔴 RED AGENT ATTACKING...", RED)
        run_script("run_red.py")

        # Check if Red Team found an exploit
        if os.path.exists("shared/exploit.json"):
            log(round_num, "💥 VULNERABILITY DETECTED! Deploying Blue Team...", BLUE)

            # Run Blue Team
            run_script("run_blue.py")

            # Wait for Uvicorn to reload the code
            print("⏳ Waiting for system patch to deploy...")
            time.sleep(3)

            log(round_num, "🛡️ PATCH APPLIED. System Hardened.", GREEN)
            print("--------------------------------------------------")

        else:
            # If Red Team failed, the system is secure!
            log(round_num, "✅ RED AGENT DEFEATED. SYSTEM UNBREAKABLE.", GREEN)
            print(f"{GREEN}🏆 VICTORY: The Autonomous Defense System won in Round {round_num - 1}!{RESET}")
            break


if __name__ == "__main__":
    start_war()