import sys
import os
import requests
import json
import time
# Now this import will work because of the hack above
from shared.llm_core import ask_llm_json

TARGET_URL = "http://localhost:8000"
ENDPOINT = "/buy"


def log(step, message, status="INFO"):
    colors = {"INFO": "\033[94m", "SUCCESS": "\033[92m", "FAIL": "\033[91m", "RESET": "\033[0m"}
    print(f"{colors.get(status, '')}[{step}] {message}{colors['RESET']}")


def generate_ai_payloads():
    log("THINK", "Analyzing API surface for logic flaws...", "INFO")

    system_role = "You are an advanced Penetration Testing AI. Your goal is to find logic bugs, integer overflows, and business logic bypasses."

    target_desc = """
        Target API: POST /buy
        Schema: {"item": string, "quantity": integer}
        Valid Items: "apple", "banana", "flag"  <-- ADD THIS LINE!
        Context: A simple shop. User has a wallet balance. 
        Goal: Exploit the logic to increase wallet balance or buy items for free.
        Constraints: Return a JSON object with a key 'payloads' which is a list of JSON payloads to test.
        """

    response = ask_llm_json(system_role, target_desc)

    if "payloads" in response:
        log("THINK", f"AI generated {len(response['payloads'])} attack vectors.", "SUCCESS")
        return response['payloads']
    else:
        log("ERROR", "AI failed to generate valid payloads.", "FAIL")
        return []


def attack():
    log("INIT", "Starting INTELLIGENT Red Agent...", "INFO")

    try:
        initial_balance = requests.get(f"{TARGET_URL}/wallet").json()["balance"]
        log("SCAN", f"Initial Wallet Balance: ${initial_balance}", "INFO")
    except Exception:
        log("FATAL", "Target app is down! Run 'uvicorn target_app.main:app --reload'", "FAIL")
        return

    payloads = generate_ai_payloads()

    for payload in payloads:
        log("ATTACK", f"Testing payload: {payload}", "INFO")

        try:
            requests.post(f"{TARGET_URL}{ENDPOINT}", json=payload)
            current_balance = requests.get(f"{TARGET_URL}/wallet").json()["balance"]

            if current_balance > initial_balance:
                log("PWNED", f"CRITICAL VULNERABILITY FOUND!", "SUCCESS")
                log("PROOF", f"Balance increased from {initial_balance} to {current_balance}", "SUCCESS")

                exploit_artifact = {
                    "vulnerability_type": "Logic/Financial",
                    "endpoint": ENDPOINT,
                    "payload": payload,
                    "severity": "Critical",
                    "description": "AI detected that negative quantities reverse the transaction flow."
                }

                with open("shared/exploit.json", "w") as f:
                    json.dump(exploit_artifact, f, indent=2)

                log("EXPORT", "Exploit saved. Handoff to Blue Agent.", "SUCCESS")
                return

            if current_balance < initial_balance:
                pass

        except Exception as e:
            log("ERROR", str(e), "FAIL")

        time.sleep(0.5)

    log("END", "Attack loop finished.", "INFO")


if __name__ == "__main__":
    attack()