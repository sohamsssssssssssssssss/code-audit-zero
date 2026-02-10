# 🛡️ Code-Audit Zero: Autonomous Cyber War

> **The First Self-Healing, Mathematically Proven Cyber-Range.**
> *Imagine Cup 2026 Submission*

**Code-Audit Zero** is a closed-loop cyber warfare simulation where AI Agents battle for control of a live financial application.
- 🔴 **Red Agent**: Attacts the system using a multi-step Kill Chain (Recon -> Theft -> Escalation).
- 🔵 **Blue Agent**: Defends the system by hot-patching code and **mathematically proving** security with Z3.
- 🟡 **Gold Agent**: The Judge. Runs regression tests and replays exploits to validate every patch.

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key (Set in `.env` or environment)

### Installation
1.  **Clone & Build**:
    ```bash
    git clone https://github.com/your-repo/code-audit-zero.git
    cd code-audit-zero
    docker-compose up --build
    ```

2.  **Launch Dashboard**:
    Open [http://localhost:8501](http://localhost:8501) in your browser.

3.  **Start the War**:
    - Click **🔄 SYSTEM RESET** to clear previous memory.
    - Click **🔴 INITIATE ATTACK** to unleash the Red Agent.

---

## 🏗️ Architecture

| Service | Technology | Role |
| :--- | :--- | :--- |
| **Target App** | FastAPI, Python | The vulnerable banking application holding the "Vault". |
| **Red Agent** | OpenAI GPT-4o, Python | Autonomous Attacker. Remembers past failures (Redis Memory). |
| **Blue Agent** | Z3 Prover, OpenAI | Autonomous Defender. Patches code & verifies logic. |
| **Gold Agent** | Pytest, Requests | The Referee. Decides if a patch is valid (PASS/FAIL). |
| **Redis** | Redis | Message Bus (Pub/Sub) & State Persistence. |
| **Dashboard** | Streamlit | Command Center for visualizing the battle. |

---

## 🌟 Key Features

### 1. Provable Security (Z3 Integration)
We don't just "guess" if a patch works. The Blue Agent translates the Python code into mathematical constraints (SMT-LIB) and uses the **Microsoft Z3 Theorem Prover** to prove that the vulnerability (e.g., `quantity < 0`) is **UNSATISFIABLE**.

### 2. Iterative Learning Loop
Agents have long-term memory stored in Redis.
- **Red** learns from 403 Forbidden errors to stop trying patched payloads.
- **Blue** learns from bypasses to create "Hardened Patches".

### 3. Cyber Dashboard v2.0 (Battle Mode)
Watch the war unfold in real-time:
- **Battle Arena**: Red vs Blue terminal feeds.
- **Live Scoring**: Points for funds stolen vs attacks blocked.
- **The Verdict**: Gold Agent's real-time judgement overlay.

---

## 📂 Project Structure
```
.
├── blue_agent/      # Defender logic (patcher.py, z3_verifier.py)
├── red_agent/       # Attacker logic (attacker.py, kill_chain.py)
├── gold_agent/      # Judge logic (judge.py, tests/)
├── target_app/      # Vulnerable FastAPI application
├── shared/          # Shared config and logger
├── dashboard.py     # Streamlit UI
├── docker-compose.yml
└── Dockerfile.*     # Individual container builds
```

---

## 🏆 Credits
Built for **Microsoft Imagine Cup**.
- **User**: Lead Architect
- **Antigravity**: Agentic AI Co-pilot
