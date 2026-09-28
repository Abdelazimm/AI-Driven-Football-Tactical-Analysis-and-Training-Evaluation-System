"""Authenticated callback-only API hosted with the Modal project app.

Only the internal worker route is exposed. Public job and result routes remain
served by the existing backend and use its Supabase-backed repositories.
"""
import modal
from fastapi import FastAPI

from modal_app.app import app, worker_image, worker_secret


@app.function(image=worker_image, secrets=[worker_secret], timeout=120)
@modal.asgi_app()
def callback_api():
    from backend.app.api.internal import router

    api = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    api.include_router(router, prefix="/api/v1")
    return api
