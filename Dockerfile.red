FROM python:3.9-slim

WORKDIR /app

# 1. Install dependencies
# (We assume requirements.txt is in 'target_app' or root.
# If it's inside target_app, copy it specifically)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2. Copy the entire project context (shared, red_agent, blue_agent)
# This COPY command is moved to after the new RUN command for dependencies.
# COPY . .

# 3. Set Python path so it can find 'shared' module
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 4. # Install dependencies including the new enhancement tools
RUN pip install redis requests openai pydantic pydantic-settings colorlog watchdog semgrep bandit hypothesis

# Ensure WORKDIR is set before copying files if it was changed, though it's already /app
WORKDIR /app

# Copy the entire agent code including layers and config
COPY . .

# Start the new enhanced orchestrator
CMD ["python", "red_agent/autonomous_attacker.py"]