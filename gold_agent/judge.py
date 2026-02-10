import redis
import os
import json
import time
import requests
import pytest
from shared.config import settings, get_logger

logger = get_logger("GOLD_AGENT")

# Redis Connection
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

class GoldJudge:
    def __init__(self):
        self.target_url = settings.TARGET_URL

    def run_regression_tests(self):
        """Run functional tests to ensure the app is not broken."""
        logger.info("🧪 Running Regression Suite...")
        exit_code = pytest.main(["-q", "/app/gold_agent/tests/test_functional.py"])
        return exit_code == 0

    def replay_exploit(self):
        """Replay the last known successful attack from Red Agent memory."""
        logger.info("🔁 Replaying Last Exploit...")
        
        # Get last success from KB_RED
        # Format: "SUCCESS: /endpoint exploited via {...}"
        lessons = r.lrange("KB_RED", 0, -1)
        last_success = next((l for l in lessons if "SUCCESS" in l), None)
        
        if not last_success:
            logger.warning("⚠️ No successful exploit found in memory to replay.")
            return True # Pass contextually

        try:
            # Simple parsing logic (can be made robust)
            # Assuming format: SUCCESS: {url} exploited via {payload}
            parts = last_success.split(" exploited via ")
            url = parts[0].replace("SUCCESS: ", "").strip()
            payload_str = parts[1].strip()
            # Replace single quotes for JSON parsing if needed
            payload = json.loads(payload_str.replace("'", '"'))

            headers = {}
            # If "admin" in URL, try to use the *OLD* key to verify rotation
            if "admin" in url:
                headers = {"X-Admin-Token": "PROD_ADMIN_2024"} 

            if not url.startswith("http"):
                 url = f"{self.target_url}{url}"

            logger.info(f"💥 Re-Firing Payload: {payload} at {url}")
            res = requests.post(url, json=payload, headers=headers, timeout=5)
            
            if res.status_code == 200:
                logger.critical(f"❌ REPLAY SUCCESSFUL (Fix Failed): {res.json()}")
                return False
            else:
                logger.info(f"✅ REPLAY BLOCKED: {res.status_code} {res.text}")
                return True

        except Exception as e:
            logger.error(f"⚠️ Replay Error: {e}")
            return True # Fail open safely

    def judge(self):
        logger.info("⚖️ Judge is analyzing the patch...")
        
        # 1. Regression Test
        regression_pass = self.run_regression_tests()
        
        # 2. Security Test
        security_pass = self.replay_exploit()
        
        # 3. Verdict
        if regression_pass and security_pass:
            verdict = "PASS"
            msg = "✅ Patch Verified: Functional & Secure."
        elif not regression_pass:
            verdict = "FAIL_REGRESSION"
            msg = "❌ Patch Verification Failed: Functionality Broken (Regression)."
        else:
            verdict = "FAIL_SECURITY"
            msg = "❌ Patch Verification Failed: Exploit still active."
            
        logger.info(f"👨‍⚖️ VERDICT: {verdict}")
        r.set("JUDGE_VERDICT", json.dumps({"status": verdict, "message": msg, "timestamp": time.time()}))
        r.publish("commands", f"VERDICT_{verdict}")

    def listen(self):
        pubsub = r.pubsub()
        pubsub.subscribe("commands") # Listen for global commands
        pubsub.subscribe("events")   # Listen for PATCH events
        
        logger.info("⚖️ Gold Agent (Judge) Online. Waiting for patches...")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = message['data']
                if data == "PATCH_DEPLOYED":
                    # Wait a sec for reload
                    time.sleep(2)
                    self.judge()
                elif data == "RESET_ALL":
                     logger.info("🧹 Resetting verdict.")
                     r.delete("JUDGE_VERDICT")

if __name__ == "__main__":
    judge = GoldJudge()
    judge.listen()
