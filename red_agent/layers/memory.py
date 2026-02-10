import json
import time
from typing import List, Dict, Any, Optional

class AttackMemory:
    def __init__(self, redis_client, logger):
        self.redis = redis_client
        self.logger = logger

    def record_attack(self, type: str, success: bool, payload: Any = None, impact: str = "LOW"):
        """Store attack result and update statistics matching red:attacks:{attack_type} structure"""
        key = f"red:attacks:{type}"
        
        self.redis.hincrby(key, "total_attempts", 1)
        if success:
            self.redis.hincrby(key, "successful", 1)
            self.redis.hset(key, "last_success", time.strftime("%Y-%m-%dT%H:%M:%S"))
        else:
            self.redis.hincrby(key, "blocked_count", 1)
            self.redis.hset(key, "last_blocked", time.strftime("%Y-%m-%dT%H:%M:%S"))
            if payload:
                # Store failed payloads to avoid repeating them specifically
                self.redis.sadd(f"{key}:failed_payloads", str(payload))

        # Update success rate hash field as per spec
        stats = self.redis.hgetall(key)
        attempts = int(stats.get("total_attempts", 1))
        successful = int(stats.get("successful", 0))
        rate = successful / attempts
        self.redis.hset(key, "success_rate", str(rate))

        self.logger.info(f"💾 [MEMORY] Updated stats for {type}:")
        self.logger.info(f"  • Success Rate: {rate*100:.1f}%")
        self.logger.info(f"  • Total Attempts: {attempts}")

    def is_payload_failed(self, type: str, payload: Any) -> bool:
        """Check if a specific payload has failed before for this attack type"""
        return self.redis.sismember(f"red:attacks:{type}:failed_payloads", str(payload))

    def get_attack_success_rate(self, type: str) -> float:
        rate = self.redis.hget(f"red:attacks:{type}", "success_rate")
        return float(rate) if rate else 0.0

    def get_blocked_count(self, type: str) -> int:
        count = self.redis.hget(f"red:attacks:{type}", "blocked_count")
        return int(count) if count else 0

    def is_recently_blocked(self, type: str, threshold_minutes: int = 5) -> bool:
        """Check if attack was recently blocked by Blue Agent (default 5 mins)"""
        # Check if permanently patched first
        if self.redis.hget(f"red:attacks:{type}", "status") == "patched":
            return True

        last_blocked_str = self.redis.hget(f"red:attacks:{type}", "last_blocked")
        if not last_blocked_str:
            return False
        
        try:
            last_blocked_time = time.mktime(time.strptime(last_blocked_str, "%Y-%m-%dT%H:%M:%S"))
            elapsed = time.time() - last_blocked_time
            return elapsed < (threshold_minutes * 60)
        except:
            return False

    def mark_patched(self, vuln_type: str):
        """Mark a vulnerability type as permanently patched by Blue Agent"""
        key = f"red:attacks:{vuln_type}"
        self.redis.hset(key, "status", "patched")
        self.redis.hset(key, "last_blocked", time.strftime("%Y-%m-%dT%H:%M:%S"))
        self.logger.critical(f"🛡️ [MEMORY] Vulnerability {vuln_type} has been PATCHED by Blue Agent.")

    def prioritize_attacks(self, vulns: List[Any]) -> List[Any]:
        """
        Sort vulnerabilities by probability of success using EXACT formula:
        score = (severity * 10) + (success_rate * 100) - (blocked_penalty * 50)
        """
        scored_vulns = []
        self.logger.info("🧠 [MEMORY] Attack scoring:")
        
        severity_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        
        for v in vulns:
            # Step 1: Filter Recently Blocked or Patched
            if self.is_recently_blocked(v.type):
                status = self.redis.hget(f"red:attacks:{v.type}", "status")
                if status == "patched":
                    self.logger.info(f"  • {v.type}: [BLOCKED] Permanently patched by Blue Agent.")
                else:
                    self.logger.info(f"  • {v.type}: [SKIPPED] Recently blocked by Blue Agent.")
                continue
                
            # Step 2: Scoring
            sev_val = severity_map.get(v.severity.value if hasattr(v.severity, 'value') else v.severity, 1)
            severity_score = sev_val * 10
            success_rate = self.get_attack_success_rate(v.type)
            success_score = success_rate * 100
            
            blocked_count = self.get_blocked_count(v.type)
            blocked_penalty = min(blocked_count * 5, 50) 
            
            total_score = severity_score + success_score - blocked_penalty
            scored_vulns.append((v, total_score))
            
            self.logger.info(f"  • {v.type}: score = {total_score:.1f} (severity={v.severity.value}, rate={success_rate:.2f}, blocked={blocked_count})")
        
        scored_vulns.sort(key=lambda x: x[1], reverse=True)
        results = [x[0] for x in scored_vulns]
        
        if results:
            self.logger.info(f"🎯 [BRAIN] Selected top choice: {results[0].type}")
        
        return results
