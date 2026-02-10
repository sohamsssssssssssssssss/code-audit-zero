# 🔴 Red Agent - Autonomous Attack Engine

The Red Agent is a sophisticated, multi-layered autonomous system designed for zero-day vulnerability identification and exploitation. It moves beyond simple LLM reasoning by integrating professional security tools and a persistent learning memory.

## 🚀 What it does
The agent operates through four primary layers, forming a complete cyber-kill-chain:

1.  **Static Analysis (Reconnaissance)**: Uses Semgrep and Bandit to scan source code for patterns indicating vulnerabilities (SQLi, IDOR, hardcoded secrets).
2.  **Exploit Validation (Exploitation)**: Automatically generates HTTP payloads based on discovered vulnerabilities and tests them against the live application.
3.  **Adaptive Fuzzer (Escalation)**: Uses `Hypothesis` for property-based testing to discover complex logic flaws and edge cases that static analysis might miss.
4.  **Attack Memory (Learning)**: A Redis-backed knowledge system that tracks success/failure rates, adapts future strategies, and avoids patched vulnerabilities.

## 🛠️ Quick Start

### Build and Run
```bash
docker-compose up -d --build red_agent
```

### Initiate an Attack Round
```bash
docker exec cyber_redis redis-cli publish commands START_RED
```

### Monitor Activities
```bash
docker logs -f red_agent
```

## 🧠 The "Brain"
The Red Agent uses a decision-making formula to prioritize attacks:
`score = (severity * 10) + (success_rate * 100) - (blocked_penalty * 50)`

This ensures the agent always pursues the most impactful and likely-to-succeed vulnerabilities first, while automatically pivoting when a defense is detected.
