import json
import os

EXPLOIT_PATH = "shared/exploit.json"
TARGET_FILE = "target_app/main.py"


def log(step, message, status="INFO"):
    colors = {"INFO": "\033[96m", "SUCCESS": "\033[92m", "FAIL": "\033[91m", "RESET": "\033[0m"}
    print(f"{colors.get(status, '')}[{step}] {message}{colors['RESET']}")


def patch():
    log("INIT", "Blue Agent (Patcher v2) started...", "INFO")

    if not os.path.exists(EXPLOIT_PATH):
        log("ERROR", "No exploit found!", "FAIL");
        return

    with open(TARGET_FILE, "r") as f:
        lines = f.readlines()

    # 1. Identify the Injection Point
    # We look for the line where 'total_cost' is calculated
    target_line_index = -1
    indentation = ""

    for i, line in enumerate(lines):
        if "total_cost = item_price * order.quantity" in line:
            target_line_index = i
            # Capture the exact whitespace (tabs/spaces) used on that line
            indentation = line.split("total_cost")[0]
            break

    if target_line_index == -1:
        log("ERROR", "Could not find injection point.", "FAIL");
        return

    # 2. Construct the Patch (Respecting Indentation)
    # We insert the check BEFORE the calculation, using the SAME indentation
    patch_lines = [
        f"{indentation}# SECURITY PATCH (Auto-Generated)\n",
        f"{indentation}if order.quantity <= 0:\n",
        f"{indentation}    raise HTTPException(status_code=400, detail='Invalid quantity')\n"
    ]

    # Check if already patched to avoid duplicates
    if "SECURITY PATCH" in lines[target_line_index - 1]:
        log("SKIP", "Patch already applied.", "SUCCESS");
        return

    # 3. Apply Patch
    # Insert our new lines before the target line
    for line in reversed(patch_lines):
        lines.insert(target_line_index, line)

    with open(TARGET_FILE, "w") as f:
        f.writelines(lines)

    log("APPLY", "Patch applied with correct indentation.", "SUCCESS")


if __name__ == "__main__":
    patch()