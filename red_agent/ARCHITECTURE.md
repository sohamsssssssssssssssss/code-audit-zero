# 🏗️ Red Agent Architecture

This document provides a technical deep dive into the Red Agent's multi-layered autonomous engine.

## 🗺️ System Overview

The Red Agent is designed as a modular state machine that transitions through the phases of a cyber-attack.

### Attack Phases
- **RECONNAISSANCE**: Static code analysis to identify potential entry points.
- **EXPLOITATION**: Live testing of identified vulnerabilities using template-based payloads.
- **ESCALATION**: Fuzzing sensitive endpoints to find logic flaws or privilege escalation.
- **PERSISTENCE**: Maintaining a presence and harvesting data (simulated).

## 📚 Component Breakdown

### Layer 1: Static Scanner (`layers/static_scanner.py`)
- **Tools**: Semgrep, Bandit.
- **Logic**: Iterates through the target codebase, applying custom rules defined in `config/semgrep_rules.yml`.
- **Output**: A prioritized list of `Vulnerability` objects containing file path, line number, severity, and CWE ID.

### Layer 2: Exploit Validator (`layers/exploit_validator.py`)
- **Action**: Takes a `Vulnerability` object and selects a payload from `exploits/` or `config/attack_templates.json`.
- **Verification**: Executes an HTTP request. Success is determined by response codes, timing, or presence of "stolen" data (e.g., passwords in response).

### Layer 3: Adaptive Fuzzer (`layers/fuzzer.py`)
- **Tool**: Hypothesis (Property-based testing).
- **Goal**: Discover "off-by-one" errors, integer overflows, or negative quantity logic flaws in endpoints like `/buy` or `/transfer`.

### Layer 4: Attack Memory (`layers/memory.py`)
- **Storage**: Redis (HA-ready).
- **Data Structure**: `red:attacks:{type}` hash containing:
  - `total_attempts`: Counter for all tries.
  - `successful`: Counter for exploits that worked.
  - `success_rate`: Calculated probability.
  - `last_blocked`: Timestamp of most recent failure (used for penalty logic).

## 🧠 Decision Algorithm

The orchestrator uses the following scoring logic to decide which vulnerability to attack next:

```python
priority_score = (vuln.severity * 10) + (memory.success_rate * 100) - (memory.blocked_penalty)
```

- **Severity**: Critical (40 pts) down to Info (0 pts).
- **Success Rate**: 0.0 to 1.0 (maps to 0-100 pts).
- **Blocked Penalty**: Subtracts up to 50 pts if the attack was recently blocked by the Blue Agent.

## 🔗 Integration with Blue Agent
The Red Agent publishes successful exploits to the `vulnerability_feed` channel in Redis. The Blue Agent listens to this feed to prioritize its automated patching logic.
