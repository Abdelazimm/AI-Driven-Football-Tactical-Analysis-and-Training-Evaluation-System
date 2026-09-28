"""
Modal Worker Entrypoint.
Provides entrypoint routines for triggering remote analysis execution or running diagnostics.
Governed by P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.
"""
import sys
from datetime import datetime, timezone
from typing import Dict, Any

from modal_app.app import app
from modal_app.worker import execute_analysis_worker, infrastructure_smoke, m2_model_preflight, m2_runtime_preflight
from modal_app.callback_api import callback_api


@app.local_entrypoint()
def main(job_id: str = "entrypoint_smoke", session_id: str = "session_smoke"):
    """
    Local CLI entrypoint for testing remote worker connectivity.
    Invoked via: modal run modal_app/entrypoint.py
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    print(f"Invoking infrastructure smoke via Modal entrypoint ({job_id})...")
    res = infrastructure_smoke.remote({
        "test_id": job_id,
        "client_timestamp": now_iso,
    })
    print(f"Modal Entrypoint Response: {res}")
