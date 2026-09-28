"""
Internal worker endpoints.
Dedicated to authenticated serverless worker callbacks (e.g. Modal).
Strictly protected via internal backend secret; NOT a public user API.
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from backend.app.schemas.dispatch import (
    WorkerProgressCallbackRequest,
    WorkerProgressCallbackResponse,
)
from backend.app.schemas.error import ApiError
from backend.app.services.dispatch_service import (
    AnalysisDispatchService,
    DispatchServiceError,
)
from backend.app.api.deps import (
    get_dispatch_service,
    verify_worker_secret,
)

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post(
    "/jobs/{job_id}/progress",
    response_model=WorkerProgressCallbackResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_worker_secret)],
    responses={
        400: {"model": ApiError, "description": "Validation or ownership mismatch"},
        401: {"description": "Invalid or missing worker callback secret"},
        404: {"model": ApiError, "description": "Job or dispatch not found"},
    },
)
async def report_worker_progress(
    job_id: str,
    payload: WorkerProgressCallbackRequest,
    dispatch_service: AnalysisDispatchService = Depends(get_dispatch_service),
):
    """
    Receive authenticated progress and state updates from compute workers.
    Validates job/dispatch association, prevents reopening terminal states,
    and updates durable job lifecycle and dispatch status in Supabase.
    """
    try:
        updated_job, updated_dispatch, is_replay = await dispatch_service.handle_worker_callback(
            job_id=job_id,
            callback=payload,
        )
        msg = (
            "Callback acknowledged; job already in terminal state (no-op)."
            if is_replay
            else "Progress recorded successfully."
        )
        return WorkerProgressCallbackResponse(
            job_id=updated_job.id,
            dispatch_id=updated_dispatch.id,
            dispatch_state=updated_dispatch.state,
            job_status=updated_job.status,
            current_stage=updated_job.current_stage,
            progress_percent=updated_job.progress_percent,
            message=msg,
        )
    except DispatchServiceError as dse:
        error = ApiError(
            code=dse.code,
            message=dse.message,
            details=dse.details,
        )
        return JSONResponse(status_code=dse.status_code, content=error.model_dump())
