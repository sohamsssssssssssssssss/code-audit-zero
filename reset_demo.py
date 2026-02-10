import os
import redis
import json
from shared.config import settings

def reset():
    print("🔄 Resetting Dojo Environment...")

    # 1. Restore the Vulnerable Code (Full schema with IDOR/Vault)
    vulnerable_code = """
from fastapi import FastAPI, HTTPException, Header
import redis
import os
import json
from shared.schemas import AttackPayload
from typing import Optional

app = FastAPI()

# Connect to Redis for Persistent State
redis_host = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

# Helper functions for state
def get_state(key: str, default: dict):
    val = r.get(key)
    if val:
        return json.loads(val)
    r.set(key, json.dumps(default))
    return default

def set_state(key: str, value: dict):
    r.set(key, json.dumps(value))

# Database simulation (Static)
users_db = {
    1: {"username": "alice", "is_admin": False, "role": "user"},
    2: {"username": "bob", "is_admin": False, "role": "user"},
    3: {"username": "charlie", "is_admin": True, "secret_key": "PROD_ADMIN_2024", "role": "admin"}
}

@app.get("/wallet")
def get_wallet():
    return get_state("app_wallet", {"balance": 100})

@app.get("/vault")
def get_vault():
    return get_state("app_vault", {"admin_fund": 10000})

@app.get("/users/{user_id}")
def get_user_profile(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.post("/buy")
def buy(payload: AttackPayload):
    wallet = get_state("app_wallet", {"balance": 100})
    if payload.quantity is None:
        raise HTTPException(status_code=400, detail="Quantity required")
    wallet["balance"] -= payload.quantity * 10
    set_state("app_wallet", wallet)
    return {"status": "success", "new_balance": wallet["balance"]}

@app.post("/admin/withdraw")
def admin_withdraw(payload: AttackPayload, x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != "PROD_ADMIN_2024":
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid Admin Token")
    
    wallet = get_state("app_wallet", {"balance": 100})
    vault = get_state("app_vault", {"admin_fund": 10000})
    
    amount = payload.quantity or 0
    if vault["admin_fund"] < amount:
        raise HTTPException(status_code=400, detail="Insufficient Vault funds")
    
    vault["admin_fund"] -= amount
    wallet["balance"] += amount
    
    set_state("app_wallet", wallet)
    set_state("app_vault", vault)
    
    return {"status": "success", "new_balance": wallet["balance"], "vault_remaining": vault["admin_fund"]}
"""
    # Adjust path if running inside Docker vs Local
    target_path = "code-audit-zero/target_app/main.py"
    if not os.path.exists("code-audit-zero"):
        target_path = "/app/target_app/main.py"

    with open(target_path, "w") as f:
        f.write(vulnerable_code.strip())
    print("✅ Target App reverted to VULNERABLE state.")

    # 2. Clear Redis Data
    try:
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        r.delete(
            'red_logs', 'blue_logs', 'exploits', 'z3_proof', 
            'KB_RED', 'KB_BLUE', 'PATCH_HISTORY',
            'app_wallet', 'app_vault'
        )
        print("✅ Redis logs and application state cleared.")
    except Exception as e:
        print(f"⚠️ Failed to clear Redis: {e}")

if __name__ == "__main__":
    reset()