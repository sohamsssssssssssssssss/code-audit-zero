import json
import os
import time

# Import the Brain
from shared.llm_core import ask_llm

TARGET_FILE = "target_app/main.py"
EXPLOIT_FILE = "shared/exploit.json"


def log(step, message, status="INFO"):
    colors = {"INFO": "\033[94m", "SUCCESS": "\033[92m", "FAIL": "\033[91m", "RESET": "\033[0m"}
    print(f"{colors.get(status, '')}[{step}] {message}{colors['RESET']}")


def patch():
    log("INIT", "Starting INTELLIGENT Blue Agent...", "INFO")

    # 1. Check if we have work to do
    if not os.path.exists(EXPLOIT_FILE):
        log("SLEEP", "No active exploits found. System is secure.", "INFO")
        return

    # 2. Load the Evidence
    with open(EXPLOIT_FILE, "r") as f:
        exploit_data = json.load(f)

    log("ALERT", f"Incoming Report: {exploit_data['vulnerability_type']} detected!", "FAIL")
    log("ANALYSIS", f"Payload used: {exploit_data['payload']}", "INFO")

    # 3. Read the Vulnerable Code
    with open(TARGET_FILE, "r") as f:
        source_code = f.read()

    # 4. Ask GPT-4o to Fix It
    log("THINK", "Consulting AI Security Architect for a fix...", "INFO")

    system_role = "You are a Senior Python Security Engineer. Your goal is to patch vulnerabilities."

    prompt = f"""
    The following Python FastAPI code has a critical vulnerability.

    VULNERABILITY REPORT:
    {json.dumps(exploit_data, indent=2)}

    SOURCE CODE:
    {source_code}

    TASK:
    Rewrite the 'buy_item' function to prevent this exploit. 
    Ensure you validate inputs (negative numbers, insufficient funds).
    Return ONLY the raw Python code for the 'buy_item' function. 
    Do not include markdown formatting (like ```python).
    """

    # Call the Brain
    fix_code = ask_llm(system_role, prompt)

    # Clean up the response (remove backticks if the AI added them)
    fix_code = fix_code.replace("```python", "").replace("```", "").strip()

    if "def buy_item" not in fix_code:
        log("ERROR", "AI failed to generate a valid function.", "FAIL")
        return

    # 5. Apply the Patch (Surgical Replacement)
    # We will replace the OLD buy_item function with the NEW AI-generated one.
    # A simple string replace works for this hackathon MVP.

    # We locate the start of the function in the original file
    new_source = source_code.replace(
        source_code.split("@app.post(\"/buy\")")[1],  # Everything after the decorator
        "\n" + fix_code  # Replace with new code
    )

    # If the simple replace failed (because of whitespace issues), we append it (MVP Hack)
    # But let's try a safer full-file write for now if the structure is simple.

    with open(TARGET_FILE, "w") as f:
        f.write(new_source)

    log("APPLY", "Patch applied successfully.", "SUCCESS")

    # 6. Delete the ticket so we don't patch twice
    os.remove(EXPLOIT_FILE)
    log("CLEANUP", "Exploit artifact resolved and removed.", "INFO")


if __name__ == "__main__":
    patch()