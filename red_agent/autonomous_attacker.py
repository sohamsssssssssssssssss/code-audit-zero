import time
import redis
import json
import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from shared.config import settings, get_logger
from shared.redis_client import publish_exploit
from layers.static_scanner import StaticScanner, Severity
from layers.exploit_validator import ExploitValidator
from layers.fuzzer import AdaptiveFuzzer
from layers.memory import AttackMemory

logger = get_logger("RED_AGENT")

class AttackPhase(Enum):
    RECONNAISSANCE = 1
    EXPLOITATION = 2
    ESCALATION = 3
    PERSISTENCE = 4

class RedAgentBrain:
    """Decision-making logic for prioritizing attacks"""
    @staticmethod
    def decide_next_attack(vulnerabilities, memory):
        # Already implemented in AttackMemory.prioritize_attacks
        return memory.prioritize_attacks(vulnerabilities)

class AutonomousAttacker:
    def __init__(self):
        self.redis = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        self.memory = AttackMemory(self.redis, logger)
        self.scanner = StaticScanner(logger)
        self.validator = ExploitValidator(settings.TARGET_URL, logger, memory=self.memory)
        self.fuzzer = AdaptiveFuzzer(settings.TARGET_URL, logger)
        self.target_code_path = "/app/target_app"
        self.current_phase = AttackPhase.RECONNAISSANCE

    def execute_round(self):
        """Execute one full cyber-kill-chain round using state transitions"""
        round_id = int(self.redis.incr("red:round_id"))
        logger.info(f"🚀 [RED AGENT] Starting Attack Round #{round_id}")
        self.current_phase = AttackPhase.RECONNAISSANCE
        
        # 1. LAYER 1: RECONNAISSANCE
        logger.info(f"📡 [RED AGENT] Phase: {self.current_phase.name}")
        vulns = self.scanner.scan_codebase(self.target_code_path)
        
        # Transition to EXPLOITATION
        self.current_phase = AttackPhase.EXPLOITATION
        logger.info(f"💥 [RED AGENT] Phase: {self.current_phase.name}")
        
        # 2. LAYER 4: PRIORITIZATION
        prioritized_vulns = self.memory.prioritize_attacks(vulns)
        
        # 3. LAYER 2: EXPLOITATION
        exploit_results = []
        for vuln in prioritized_vulns[:3]:
            result = self.validator.validate_exploit(vuln)
            if result:
                exploit_results.append(result)
                self.memory.record_attack(vuln.type, result.success, result.payload)
                if result.success:
                    logger.critical(f"💥 [IMPACT] {vuln.type} EXPLOITED successfully on {vuln.file_path}")
                    self._report_success(vuln, result)

        # Transition Logic
        successful = [r for r in exploit_results if r.success]
        if successful:
            self.current_phase = AttackPhase.ESCALATION
        else:
            self.current_phase = AttackPhase.RECONNAISSANCE
            logger.info("ℹ️ [RED AGENT] No successful exploits. Returning to Reconnaissance.")
            return

        # 4. LAYER 3: ESCALATION (Fuzzing)
        logger.info(f"🔥 [RED AGENT] Phase: {self.current_phase.name}")
        fuzz_findings = self.fuzzer.fuzz_vulnerable_endpoints()
        for finding in fuzz_findings:
            logger.critical(f"🔥 [IMPACT] Fuzzing discovered {finding['type']} on {finding['endpoint']}")
            self._report_fuzz_success(finding)
            self.memory.record_attack("LOGIC_FLAW", True, finding['payload'], impact="CRITICAL")

        # PERSISTENCE (Simulation)
        self.current_phase = AttackPhase.PERSISTENCE
        logger.info(f"🕵️ [RED AGENT] Phase: {self.current_phase.name}")
        logger.info("Maintaining access and harvesting target data...")
        
        logger.info(f"🏁 [RED AGENT] Round #{round_id} Complete.")

    def _report_success(self, vuln, result):
        event = {
            "severity": "Critical",
            "vulnerability_type": vuln.type,
            "target_endpoint": vuln.file_path,
            "payload": result.payload,
            "description": f"Layered Attack: {vuln.description}"
        }
        publish_exploit(event)

    def _report_fuzz_success(self, finding):
        event = {
            "severity": finding['impact'],
            "vulnerability_type": finding['type'],
            "target_endpoint": finding['endpoint'],
            "payload": finding['payload'],
            "description": finding['description']
        }
        publish_exploit(event)

def listen_and_attack():
    while True:
        try:
            r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
            pubsub = r.pubsub()
            pubsub.subscribe("commands", "patches:deployed")
            agent = AutonomousAttacker()
            logger.info("🔴 Enhanced Red Agent (Layered Architecture) online and listening.")
            
            for message in pubsub.listen():
                if message['type'] != 'message':
                    continue
                
                channel = message['channel']
                data = message['data']
                
                if channel == "commands" and data == "START_RED":
                    try:
                        agent.execute_round()
                    except Exception as e:
                        logger.error(f"❌ Round Failed: {e}")
                
                elif channel == "patches:deployed":
                    try:
                        patch_info = json.loads(data)
                        vuln_id = patch_info.get("vuln_id", "")
                        status = patch_info.get("status", "")
                        
                        if status == "patched":
                            # Simple mapping logic for demo: map ID substring to type
                            if "sql" in vuln_id.lower():
                                agent.memory.mark_patched("SQL_INJECTION")
                            elif "idor" in vuln_id.lower():
                                agent.memory.mark_patched("IDOR")
                            elif "secret" in vuln_id.lower():
                                agent.memory.mark_patched("HARDCODED_SECRET")
                            else:
                                logger.warning(f"⚠️ Received patch for unknown vuln_id: {vuln_id}")
                    except Exception as e:
                        logger.error(f"⚠️ Failed to process patch event: {e}")

        except redis.ConnectionError:
            logger.error("📡 Lost connection to Redis. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"⚠️ Unexpected error in listener: {e}")
            time.sleep(5)

if __name__ == "__main__":
    listen_and_attack()
