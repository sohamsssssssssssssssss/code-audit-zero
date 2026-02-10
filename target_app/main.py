from fastapi import FastAPI, HTTPException, Header, Query
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

@app.get("/logs")
def get_logs(file: str = Query(..., description="The log file to view")):
    """VULNERABLE: Direct path concatenation allows Path Traversal"""
    # Force absolute path from /app to be 100% sure for demo
    base_dir = "/app/target_app/logs"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
        
    log_path = os.path.abspath(os.path.join(base_dir, file))
    
    try:
        with open(log_path, "r") as f:
            return {
                "file": file, 
                "log_path": log_path,
                "content": f.read()
            }
    except Exception as e:
        raise HTTPException(status_code=404, detail={
            "error": str(e),
            "attempted_path": log_path,
            "cwd": os.getcwd(),
            "base_dir_exists": os.path.exists(base_dir)
        })