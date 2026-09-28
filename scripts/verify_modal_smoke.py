"""
Modal CPU Infrastructure Smoke Verification Script.
Step 16 & 27 of Phase 4A.
Tests remote connectivity and CPU worker execution without AI models or GPUs.
"""
import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.getcwd()))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass



from backend.app.services.modal_client import (
    ProductionModalClient,
    ModalAuthenticationError,
    ModalSubmissionError,
)
from modal_app.contracts import InfrastructureSmokeRequest, InfrastructureSmokeResponse


def run_smoke_test():
    print("=== MODAL CPU INFRASTRUCTURE VERIFICATION ===")
    client = ProductionModalClient()

    is_configured = client.is_configured()
    print(f"Modal auth configured: {is_configured}")

    if not is_configured:
        print("MODAL_PACKAGE: INSTALLED")
        print("MODAL_AUTH: NOT CONFIGURED")
        print("\nAction required from user to complete live verification:")
        print("Set real MODAL_TOKEN_ID and MODAL_TOKEN_SECRET in .env, or run `python -m modal token set`.")
        return False

    print("MODAL_PACKAGE: INSTALLED")
    print("MODAL_AUTH: CONFIGURED")

    test_id = f"smoke_{uuid.uuid4().hex[:8]}"
    client_ts = datetime.now(timezone.utc).isoformat()
    if client_ts.endswith("+00:00"):
        client_ts = client_ts[:-6] + "Z"

    payload = InfrastructureSmokeRequest(
        test_id=test_id,
        client_timestamp=client_ts,
        marker="PHASE_4A_INFRA_SMOKE",
    ).model_dump()

    print(f"Dispatching lightweight CPU function (test_id: {test_id})...")
    try:
        import modal
        from modal_app.app import app
        from modal_app.worker import infrastructure_smoke

        with modal.enable_output():
            with app.run():
                raw_res = infrastructure_smoke.remote(payload)

        # Contract Validation against InfrastructureSmokeResponse
        smoke_resp = InfrastructureSmokeResponse(**raw_res)
        print("Remote invocation SUCCEEDED and validated against InfrastructureSmokeResponse!")
        print(f"Status: {smoke_resp.status}")
        print(f"Server timestamp: {smoke_resp.server_timestamp}")
        print(f"Container Python version: {smoke_resp.python_version}")
        print(f"CPU-only confirmed: {smoke_resp.cpu_only}")
        print(f"Marker confirmed: {smoke_resp.marker}")
        return True
    except ModalAuthenticationError as me:
        print(f"Modal auth failed: {me.message}")
        return False
    except ModalSubmissionError as mse:
        print(f"Modal remote invocation error: {mse.message}")
        return False
    except Exception as e:
        print(f"Unexpected error during Modal execution: {e}")
        return False


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
