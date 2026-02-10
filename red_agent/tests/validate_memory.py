import redis
import time
import json
import os
from shared.config import settings, get_logger
from layers.memory import AttackMemory
from layers.static_scanner import Severity

class MockVuln:
    def __init__(self, type, severity):
        self.type = type
        self.severity = severity

def validate_memory_learning():
    logger = get_logger("MEMORY_TEST")
    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
    memory = AttackMemory(r, logger)
    
    logger.info("🔍 [TEST] Starting Memory System Validation...")
    
    # 1. Clear previous stats for test keys
    test_keys = ["SQL_INJECTION", "IDOR"]
    for k in test_keys:
        r.delete(f"red:attacks:{k}")
    
    vulns = [
        MockVuln("SQL_INJECTION", Severity.CRITICAL),
        MockVuln("IDOR", Severity.HIGH)
    ]
    
    # scenario 1: Record SUCCESS for SQL_INJECTION
    logger.info("Scenario 1: Recording Success for SQL Injection...")
    memory.record_attack("SQL_INJECTION", True)
    
    # Verify SQL_INJECTION is prioritized
    prioritized = memory.prioritize_attacks(vulns)
    logger.info(f"Prioritized order: {[v.type for v in prioritized]}")
    assert prioritized[0].type == "SQL_INJECTION"
    
    # Scenario 2: Record BLOCKED for SQL_INJECTION
    logger.info("Scenario 2: Recording Blocked for SQL Injection...")
    # Simulate Blue Agent patch by recording failure
    memory.record_attack("SQL_INJECTION", False)
    
    # Verify it's still prioritized but score is slightly lower (penalty)
    # Actually, is_recently_blocked might filter it out
    is_blocked = memory.is_recently_blocked("SQL_INJECTION")
    logger.info(f"Is SQL_INJECTION recently blocked? {is_blocked}")
    
    if is_blocked:
        prioritized = memory.prioritize_attacks(vulns)
        logger.info(f"Prioritized order after block: {[v.type for v in prioritized]}")
        assert "SQL_INJECTION" not in [v.type for v in prioritized] or prioritized[0].type != "SQL_INJECTION"
    
    logger.info("✅ [TEST] Memory System Validation Passed!")

if __name__ == "__main__":
    validate_memory_learning()
