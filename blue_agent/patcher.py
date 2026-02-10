import redis
import json
import time
import ast
import os
import logging
import uuid
import re
from shared.config import settings, get_logger
from shared.llm_core import ask_llm_text
from shared.schemas import ExploitEvent
from shared.formal_prover import FormalSecurityProof

# Initialize Enterprise Logger
logger = get_logger("BLUE_AGENT")


class BlueDefenseAgent:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.pubsub = self.redis_client.pubsub()
        self.pubsub.subscribe(settings.REDIS_CHANNEL, "commands")
        self.prover = FormalSecurityProof()
        logger.info(f"🛡️ Blue Agent Online. Guarding Infrastructure...")

    def reset_system(self):
        logger.warning("🔄 System Reset Triggered. Purging all remediations & Knowledge Base...")
        
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
        target_file = "/app/target_app/main.py"
        try:
            with open(target_file, "w") as f:
                f.write(vulnerable_code.strip())
            
            # CLEAR EVERYTHING INCLUDING THE APP STATE
            self.redis_client.delete(
                'red_logs', 'blue_logs', 'exploits', 'z3_proof', 
                'KB_RED', 'KB_BLUE', 'PATCH_HISTORY',
                'app_wallet', 'app_vault'
            )
            logger.info("✅ Core code restored. Memory wiped.")
        except Exception as e:
            logger.error(f"❌ Restore failure: {e}")

    def generate_patch_prompt(self, event: ExploitEvent, current_code: str, history: str) -> str:
        history_context = f"\nPATCH HISTORY FOR THIS ENDPOINT:\n{history}" if history else ""
        
        return f"""
        You are an autonomous Cyber-Defense AI with ITERATIVE LEARNING.
        
        INCIDENT DETECTED:
        - Vulnerability: {event.vulnerability_type}
        - Vector: {event.target_endpoint}
        {history_context}

        URGENT TASK:
        Analyze the current source code and provide a secure, production-ready patch.
        DO NOT just fix the reported endpoint. Perform a FULL SECURITY AUDIT of the code.
        If you see any other vulnerabilities (like IDOR on /users or lack of auth on /wallet), FIX THEM as well.
        
        CRITICAL MANDATE: CREDENTIAL ROTATION
        - The secret "PROD_ADMIN_2024" is COMPROMISED.
        - You MUST change it in the 'users_db' dictionary to a new, secure value (e.g., "SECURE_ADMIN_V2_XYZ").
        - If you do not change this string, the attacker will just log back in.
        - This is the MOST IMPORTANT part of the patch.

        If there is a PATCH HISTORY, it means the Red Agent bypassed our previous fix. 
        You MUST identify the flaw in the previous logic and implement "Hardened Validation".
        
        SOURCE:
        {current_code}

        Return ONLY the full python file content.
        """

    def analyze_threat(self, event_data: str):
        if not event_data or not event_data.strip().startswith("{"):
            return
        
        try:
            data = json.loads(event_data)
            event = ExploitEvent(**data)
            logger.critical(f"🚨 [INCIDENT] Confirmed {event.vulnerability_type} breach on {event.target_endpoint}")

            # 1. Self-Diagnosis & History Retrieval
            logger.info("🔍 Investigating past remediations for this node...")
            target_file = "/app/target_app/main.py"
            current_code = ""
            if os.path.exists(target_file):
                with open(target_file, "r") as f:
                    current_code = f.read()

            # Check if we've patched this before
            prev_patches = self.redis_client.hget("PATCH_HISTORY", event.target_endpoint)
            if prev_patches:
                logger.warning(f"⚠️ BYPASS DETECTED! Previous fix for {event.target_endpoint} was insufficient.")

            # 2. Remediation Strategy
            logger.info("🧠 Synthesizing adaptive hardened patch...")
            patch_code = ask_llm_text(
                system_prompt="You are an expert Secure Code Reviewer with memory of past failures.",
                user_prompt=self.generate_patch_prompt(event, current_code, prev_patches)
            )
            patch_code = patch_code.replace("```python", "").replace("```", "").strip()

            if not self.validate_syntax(patch_code):
                logger.error("❌ Generated patch failed syntax validation.")
                return

            # Validate and Enforce Rotation
            # Use Regex to handle single/double quotes
            secret_pattern = re.compile(r"['\"]PROD_ADMIN_2024['\"]")
            if secret_pattern.search(patch_code):
                logger.warning("⚠️ LLM failed to rotate credential. Enforcing MANUAL ROTATION.")
                new_key = f"SECURE_{uuid.uuid4().hex[:8].upper()}"
                patch_code = secret_pattern.sub(f'"{new_key}"', patch_code)
                logger.critical(f"🔄 Credential Rotated: PROD_ADMIN_2024 -> {new_key}")
            else:
                logger.info("ℹ️ Secret already rotated or not found in patch.")

            # 3. Formal Verification
            logger.info("🔢 Validating with Z3 Prover...")
            proof = self.prover.verify_remediation(event.vulnerability_type, patch_code)
            
            if proof["proven"]:
                logger.info(f"🏆 [PROVEN] {proof['details']}")
                self.redis_client.set("z3_proof", proof["logic"])

            # 4. Deployment & Learning
            logger.warning("⚡ DEPLOYING HARDENED PATCH...")
            with open(target_file, "w") as f:
                f.write(patch_code)
            
            # Record the lesson
            lesson = f"Vulnerability: {event.vulnerability_type} | Fix: Added more robust checks | Status: Applied"
            self.redis_client.lpush("KB_BLUE", lesson)
            self.redis_client.hset("PATCH_HISTORY", event.target_endpoint, f"Last fix: {event.vulnerability_type}")
            
            # TRIGGER THE JUDGE
            self.redis_client.publish("events", "PATCH_DEPLOYED")
            
            logger.info("🛡️ Guard Hardened and Lesson Recorded. Judge Triggered.")

        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")

    def validate_syntax(self, code):
        try:
            ast.parse(code)
            return True
        except: return False

    def run_surveillance(self):
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                if message['channel'] == "commands" and message['data'] == "RESET_ALL":
                    self.reset_system()
                else:
                    self.analyze_threat(message['data'])

if __name__ == "__main__":
    agent = BlueDefenseAgent()
    agent.run_surveillance()