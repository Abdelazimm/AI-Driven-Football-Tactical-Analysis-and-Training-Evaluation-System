"""
Application API v1 router definition.
Aggregates versioned routes under /api/v1.
"""
from fastapi import APIRouter
from backend.app.api.methodologies import router as methodologies_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.sessions import router as sessions_router
from backend.app.api.internal import router as internal_router
from backend.app.api.showcase import router as showcase_router

api_router = APIRouter()
api_router.include_router(methodologies_router)
api_router.include_router(jobs_router)
api_router.include_router(sessions_router)
api_router.include_router(internal_router)
api_router.include_router(showcase_router)
