"""
Modal serverless compute client adapter.
Encapsulates all interactions with the Modal SDK behind a clean provider interface.
CRITICAL: Never exposes API tokens, secrets, or raw internal stack traces.
"""
import os
import sys
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from backend.app.schemas.dispatch import WorkerDispatchRequest


class ModalError(Exception):
    """Base exception for Modal provider operations."""
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class ModalAuthenticationError(ModalError):
    """Raised when Modal credentials or authentication tokens are missing/invalid."""
    def __init__(self, message: str = "Modal authentication is not configured."):
        super().__init__("MODAL_AUTH_MISSING", message)


class ModalSubmissionError(ModalError):
    """Raised when asynchronous dispatch to Modal fails."""
    def __init__(self, message: str, code: str = "MODAL_SUBMISSION_FAILED"):
        super().__init__(code, message)



class ModalDispatchClient(ABC):
    """Abstract interface for serverless compute execution provider."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials/environment are configured."""
        pass

    @abstractmethod
    def submit_job(self, request: WorkerDispatchRequest) -> str:
        """
        Asynchronously dispatch an analysis job to the worker.
        Returns the external provider execution ID (e.g. Modal call ID).
        """
        pass

    @abstractmethod
    def invoke_infrastructure_smoke(self, payload: dict) -> dict:
        """
        Invoke the lightweight CPU-only infrastructure smoke test.
        Returns the execution response dictionary from the worker.
        """
        pass


class ProductionModalClient(ModalDispatchClient):
    """
    Live Modal SDK implementation of ModalDispatchClient.
    Connects to real Modal serverless functions.
    """

    def _setup_modal_env(self) -> None:
        """Ensure environment variables for Modal SDK authentication."""
        try:
            from backend.app.core.config import settings
            if settings.MODAL_TOKEN_ID and not os.environ.get("MODAL_TOKEN_ID"):
                os.environ["MODAL_TOKEN_ID"] = settings.MODAL_TOKEN_ID
            if settings.MODAL_TOKEN_SECRET and not os.environ.get("MODAL_TOKEN_SECRET"):
                os.environ["MODAL_TOKEN_SECRET"] = settings.MODAL_TOKEN_SECRET
        except Exception:
            pass

    def is_configured(self) -> bool:
        """Verify presence of Modal auth tokens."""
        self._setup_modal_env()
        token_id = os.environ.get("MODAL_TOKEN_ID", "")
        token_secret = os.environ.get("MODAL_TOKEN_SECRET", "")
        if token_id and not token_id.startswith("your-") and token_secret and not token_secret.startswith("your-"):
            return True
        try:
            import modal.config
            cfg = modal.config.config
            tid = cfg.get("token_id")
            return bool(tid and not str(tid).startswith("your-"))
        except Exception:
            return False

    def submit_job(self, request: WorkerDispatchRequest) -> str:
        if not self.is_configured():
            raise ModalAuthenticationError(
                "Modal authentication is not configured. Set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET."
            )

        try:
            if not (request.dispatch_id and request.video_storage_path and request.callback_url):
                raise ModalSubmissionError("Remote dispatch requires dispatch ID, validated media path, and callback URL")
            import modal
            worker = modal.Function.from_name("football-tactical-analysis", "execute_analysis_worker")
            call = worker.spawn(request.model_dump(mode="json"))
            if not getattr(call, "object_id", None):
                raise ModalSubmissionError("Modal did not return a real worker invocation ID")
            return call.object_id
        except ModalError:
            raise
        except Exception as e:
            raise ModalSubmissionError(f"Failed to submit job to Modal: {str(e)}")

    def invoke_infrastructure_smoke(self, payload: dict) -> dict:
        if not self.is_configured():
            raise ModalAuthenticationError(
                "Modal authentication is not configured. Set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET."
            )

        try:
            import modal
            from modal_app.app import app
            from modal_app.worker import infrastructure_smoke

            with modal.enable_output():
                with app.run():
                    return infrastructure_smoke.remote(payload)
        except Exception as e:
            raise ModalSubmissionError(f"Modal infrastructure smoke call failed: {str(e)}")


class InMemoryModalClient(ModalDispatchClient):
    """
    In-memory simulation of Modal provider for isolated testing without live credentials.
    """

    def __init__(self, configured: bool = True, force_failure: bool = False):
        self._configured = configured
        self._force_failure = force_failure
        self.submitted_jobs: Dict[str, dict] = {}

    def is_configured(self) -> bool:
        return self._configured

    def set_configured(self, val: bool) -> None:
        self._configured = val

    def set_force_failure(self, val: bool) -> None:
        self._force_failure = val

    def submit_job(self, request: WorkerDispatchRequest) -> str:
        if not self._configured:
            raise ModalAuthenticationError()
        if self._force_failure:
            raise ModalSubmissionError("Simulated Modal dispatch failure.")

        exec_id = f"modal_exec_{uuid.uuid4().hex[:12]}"
        self.submitted_jobs[exec_id] = request.model_dump()
        return exec_id

    def invoke_infrastructure_smoke(self, payload: dict) -> dict:
        if not self._configured:
            raise ModalAuthenticationError()
        if self._force_failure:
            raise ModalSubmissionError("Simulated Modal infrastructure failure.")

        return {
            "test_id": payload.get("test_id", "sim_test"),
            "server_timestamp": datetime.utcnow().isoformat() + "Z",
            "environment": "in_memory_simulation",
            "python_version": sys.version.split()[0],
            "status": "SUCCESS",
            "cpu_only": True,
            "marker": payload.get("marker", "PHASE_4A_INFRA_SMOKE"),
        }
