"""Read-only routes for locally verified golden capability media."""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.app.services.golden import golden_service
from backend.app.schemas.showcase import ShowcaseResponse

router = APIRouter(prefix="/showcase", tags=["showcase"])


@router.get("", response_model=ShowcaseResponse)
def get_showcase() -> ShowcaseResponse:
    return golden_service.get_showcase_response()


@router.get("/media/{case_id}")
def get_showcase_media(case_id: str):
    case_id = case_id.upper()
    media = golden_service.resolve_media(case_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Showcase case not found")
    path = (Path(golden_service.workspace_dir) / media.fixture_path).resolve()
    golden_root = Path(golden_service.golden_dir).resolve()
    if not path.is_relative_to(golden_root) or not path.is_file():
        raise HTTPException(status_code=404, detail="Showcase media unavailable")
    if not golden_service.verify_media_integrity(case_id):
        raise HTTPException(status_code=409, detail="Showcase media integrity check failed")
    return FileResponse(path, media_type=media.media_type, filename=path.name, content_disposition_type="inline")
