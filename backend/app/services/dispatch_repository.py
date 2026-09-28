"""
Worker dispatch repository interfaces and implementations.
Handles persistence and active execution lookup of worker dispatches.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime
from supabase import Client

from backend.app.schemas.dispatch import (
    WorkerDispatch,
    WorkerDispatchState,
)

ACTIVE_DISPATCH_STATES = {
    WorkerDispatchState.CREATED,
    WorkerDispatchState.SUBMITTED,
    WorkerDispatchState.RUNNING,
}


class ActiveDispatchConflictError(Exception):
    """
    Raised when an active dispatch already exists for a job,
    enforcing the uq_active_worker_dispatch_per_job database constraint.
    """
    def __init__(self, job_id: str, existing_dispatch: Optional[WorkerDispatch] = None):
        self.job_id = job_id
        self.existing_dispatch = existing_dispatch
        super().__init__(f"An active worker dispatch already exists for job '{job_id}'.")



class WorkerDispatchRepository(ABC):
    """Abstract interface for worker dispatch records."""

    @abstractmethod
    def create_dispatch(self, dispatch: WorkerDispatch) -> WorkerDispatch:
        """Persist a new worker dispatch attempt."""
        pass

    @abstractmethod
    def get_dispatch(self, dispatch_id: str) -> Optional[WorkerDispatch]:
        """Retrieve a dispatch record by unique ID."""
        pass

    @abstractmethod
    def get_active_dispatch_for_job(self, job_id: str) -> Optional[WorkerDispatch]:
        """Retrieve an active (CREATED, SUBMITTED, RUNNING) dispatch for a job if one exists."""
        pass

    @abstractmethod
    def update_dispatch(self, dispatch: WorkerDispatch) -> WorkerDispatch:
        """Update state, provider execution ID, or errors on an existing dispatch."""
        pass

    @abstractmethod
    def list_dispatches_for_job(self, job_id: str) -> List[WorkerDispatch]:
        """List all historical dispatch attempts for a job."""
        pass


class SupabaseWorkerDispatchRepository(WorkerDispatchRepository):
    """Production Supabase PostgreSQL implementation of WorkerDispatchRepository."""

    def __init__(self, client: Client):
        self._client = client

    def create_dispatch(self, dispatch: WorkerDispatch) -> WorkerDispatch:
        payload = {
            "id": dispatch.id,
            "job_id": dispatch.job_id,
            "provider": dispatch.provider,
            "provider_execution_id": dispatch.provider_execution_id,
            "state": dispatch.state.value,
            "attempt": dispatch.attempt,
            "created_at": dispatch.created_at.isoformat(),
            "started_at": dispatch.started_at.isoformat() if dispatch.started_at else None,
            "finished_at": dispatch.finished_at.isoformat() if dispatch.finished_at else None,
            "error_code": dispatch.error_code,
            "error_message": dispatch.error_message,
        }
        try:
            res = self._client.table("worker_dispatches").insert(payload).execute()
            if not res.data:
                raise RuntimeError(f"Failed to insert worker_dispatch into Supabase: {res}")
            return dispatch
        except Exception as ex:
            err_msg = str(ex)
            # Match PostgreSQL unique violation code 23505 or constraint name uq_active_worker_dispatch_per_job
            if "23505" in err_msg or "uq_active_worker_dispatch_per_job" in err_msg or "duplicate key" in err_msg.lower():
                existing = self.get_active_dispatch_for_job(dispatch.job_id)
                raise ActiveDispatchConflictError(dispatch.job_id, existing) from ex
            raise


    def get_dispatch(self, dispatch_id: str) -> Optional[WorkerDispatch]:
        res = self._client.table("worker_dispatches").select("*").eq("id", dispatch_id).execute()
        if not res.data or len(res.data) == 0:
            return None
        return self._row_to_model(res.data[0])

    def get_active_dispatch_for_job(self, job_id: str) -> Optional[WorkerDispatch]:
        active_state_values = [s.value for s in ACTIVE_DISPATCH_STATES]
        res = (
            self._client.table("worker_dispatches")
            .select("*")
            .eq("job_id", job_id)
            .in_("state", active_state_values)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not res.data or len(res.data) == 0:
            return None
        return self._row_to_model(res.data[0])

    def update_dispatch(self, dispatch: WorkerDispatch) -> WorkerDispatch:
        payload = {
            "state": dispatch.state.value,
            "provider_execution_id": dispatch.provider_execution_id,
            "started_at": dispatch.started_at.isoformat() if dispatch.started_at else None,
            "finished_at": dispatch.finished_at.isoformat() if dispatch.finished_at else None,
            "error_code": dispatch.error_code,
            "error_message": dispatch.error_message,
        }
        res = self._client.table("worker_dispatches").update(payload).eq("id", dispatch.id).execute()
        if not res.data or len(res.data) == 0:
            raise RuntimeError(f"Failed to update worker_dispatch {dispatch.id}")
        return self._row_to_model(res.data[0])

    def list_dispatches_for_job(self, job_id: str) -> List[WorkerDispatch]:
        res = (
            self._client.table("worker_dispatches")
            .select("*")
            .eq("job_id", job_id)
            .order("created_at", desc=True)
            .execute()
        )
        if not res.data:
            return []
        return [self._row_to_model(r) for r in res.data]

    def _row_to_model(self, row: dict) -> WorkerDispatch:
        from dateutil.parser import isoparse
        return WorkerDispatch(
            id=row["id"],
            job_id=row["job_id"],
            provider=row.get("provider", "MODAL"),
            provider_execution_id=row.get("provider_execution_id"),
            state=WorkerDispatchState(row["state"]),
            attempt=row.get("attempt", 1),
            created_at=isoparse(row["created_at"]),
            started_at=isoparse(row["started_at"]) if row.get("started_at") else None,
            finished_at=isoparse(row["finished_at"]) if row.get("finished_at") else None,
            error_code=row.get("error_code"),
            error_message=row.get("error_message"),
        )


class InMemoryWorkerDispatchRepository(WorkerDispatchRepository):
    """In-memory worker dispatch repository for unit and contract testing."""

    def __init__(self):
        self._dispatches: Dict[str, WorkerDispatch] = {}

    def create_dispatch(self, dispatch: WorkerDispatch) -> WorkerDispatch:
        # Simulate PostgreSQL unique index:
        # uq_active_worker_dispatch_per_job: UNIQUE(job_id) WHERE state IN ('CREATED', 'SUBMITTED', 'RUNNING')
        if dispatch.state in ACTIVE_DISPATCH_STATES:
            for d in self._dispatches.values():
                if d.job_id == dispatch.job_id and d.state in ACTIVE_DISPATCH_STATES:
                    raise ActiveDispatchConflictError(dispatch.job_id, d)
        self._dispatches[dispatch.id] = dispatch
        return dispatch

    def get_dispatch(self, dispatch_id: str) -> Optional[WorkerDispatch]:
        return self._dispatches.get(dispatch_id)

    def get_active_dispatch_for_job(self, job_id: str) -> Optional[WorkerDispatch]:
        for d in self._dispatches.values():
            if d.job_id == job_id and d.state in ACTIVE_DISPATCH_STATES:
                return d
        return None

    def update_dispatch(self, dispatch: WorkerDispatch) -> WorkerDispatch:
        if dispatch.state in ACTIVE_DISPATCH_STATES:
            for d in self._dispatches.values():
                if d.id != dispatch.id and d.job_id == dispatch.job_id and d.state in ACTIVE_DISPATCH_STATES:
                    raise ActiveDispatchConflictError(dispatch.job_id, d)
        self._dispatches[dispatch.id] = dispatch
        return dispatch


    def list_dispatches_for_job(self, job_id: str) -> List[WorkerDispatch]:
        items = [d for d in self._dispatches.values() if d.job_id == job_id]
        items.sort(key=lambda d: d.created_at, reverse=True)
        return items

    def clear(self) -> None:
        self._dispatches.clear()
