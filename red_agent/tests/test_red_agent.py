import pytest
import redis
from shared.config import settings
from layers.static_scanner import StaticScanner, Severity
from layers.exploit_validator import ExploitValidator
from layers.fuzzer import AdaptiveFuzzer
from layers.memory import AttackMemory
from autonomous_attacker import AutonomousAttacker, AttackPhase

class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def critical(self, msg): print(f"CRITICAL: {msg}")

def test_static_scanner_initialization():
    logger = MockLogger()
    scanner = StaticScanner(logger)
    assert scanner is not None

def test_memory_scoring():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    logger = MockLogger()
    memory = AttackMemory(r, logger)
    
    # Mock some data
    class MockVuln:
        def __init__(self, type, severity):
            self.type = type
            self.severity = severity
    
    vuln = MockVuln("SQL_INJECTION", Severity.CRITICAL)
    
    # Test scoring formula
    # Reset stats
    key = f"red:attacks:SQL_INJECTION"
    r.delete(key)
    
    memory.record_attack("SQL_INJECTION", True)
    rate = memory.get_attack_success_rate("SQL_INJECTION")
    assert rate == 1.0
    
    prioritized = memory.prioritize_attacks([vuln])
    assert len(prioritized) == 1

def test_phase_transitions():
    attacker = AutonomousAttacker()
    assert attacker.current_phase == AttackPhase.RECONNAISSANCE
