import json
import os
from shared.redis_client import listen_for_exploits
from shared.schemas import ExploitEvent
from shared.config import get_logger
from blue_agent.patcher import patch
# 1. Import the new Formal Prover
from shared.formal_prover import FormalSecurityProof

logger = get_logger("BLUE_AGENT")


def handle_incident(raw_data: dict):
    logger.info("🚨 Signal Received from Redis!")
    try:
        # Validate the data
        event = ExploitEvent(**raw_data)

        # Save the exploit for the patcher to analyze
        os.makedirs("shared", exist_ok=True)
        with open("shared/exploit.json", "w") as f:
            json.dump({"payload": event.payload.model_dump()}, f)

        # 2. RUN Z3 VERIFICATION BEFORE PATCHING
        logger.info("🛡️ Initiating Formal Verification (Z3)...")
        prover = FormalSecurityProof()

        # We check if the fix is mathematically sound for the received payload
        test_qty = event.payload.quantity if hasattr(event.payload, 'quantity') else -1
        verification_result = prover.verify_remediation(test_qty)

        if verification_result["proven"]:
            logger.info(f"✅ [Z3] {verification_result['status']}: {verification_result['details']}")
            # 3. Only run the patch if Z3 gives the "Green Light"
            patch()
            logger.info("✅ Defense successful and mathematically verified.")
        else:
            logger.error(f"❌ [Z3] Verification FAILED: {verification_result['status']}")
            logger.error(f"⚠️ Counterexample found: {verification_result.get('counterexample')}")
            logger.warning("🚫 Patch aborted to prevent unsafe code deployment.")

    except Exception as e:
        logger.error(f"❌ Defense failed: {e}")


if __name__ == "__main__":
    logger.info("🛡️ BLUE AGENT: Online and waiting for Red Team...")
    listen_for_exploits(handle_incident)