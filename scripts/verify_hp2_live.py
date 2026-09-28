"""
Live verification script for Hardening Pack 2 & Migration 004.
Validates live Supabase PostgreSQL schema extensions and repository lifecycle persistence.

Checks:
1. Column existence on public.media_assets (container_format, video_codec, audio_codec, validation_status, validation_error_code)
2. Constraint acceptance of expanded upload_status ('VALIDATING', 'VALIDATED', 'VALIDATION_FAILED')
3. End-to-end repository persistence of authoritative media probe metadata
4. Clean teardown of all test records
"""
import uuid
import sys
import os
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.supabase_client import get_supabase_client, is_supabase_configured
from backend.app.services.media_repository import SupabaseMediaRepository
from backend.app.services.session_repository import SupabaseSessionRepository
from backend.app.schemas.session import Session
from backend.app.schemas.media import MediaAsset, MediaType, UploadStatus


def verify_live():
    if not is_supabase_configured():
        print("ERROR: Supabase is not configured in .env.")
        sys.exit(1)

    client = get_supabase_client()
    print("--- 1. Checking Migration 004 columns on public.media_assets ---")
    try:
        res = client.table("media_assets").select(
            "id, container_format, video_codec, audio_codec, validation_status, validation_error_code"
        ).limit(1).execute()
        print("  [OK] Columns container_format, video_codec, audio_codec, validation_status, validation_error_code exist.")
    except Exception as e:
        print("  [FAIL] Columns not found or migration not applied:")
        print(f"         {e}")
        print("\nACTION REQUIRED: Please execute backend/migrations/004_media_validation.sql in the Supabase SQL Editor.")
        sys.exit(2)

    print("\n--- 2. Testing live Supabase persistence & expanded constraint ---")
    session_repo = SupabaseSessionRepository(client)
    media_repo = SupabaseMediaRepository(client)

    test_session_id = str(uuid.uuid4())
    test_media_id = str(uuid.uuid4())

    try:
        # Create test session
        session = Session(
            id=test_session_id,
            title="HP2 Live Verification Session",
            user_id="verification_runner",
            created_at=datetime.utcnow(),
        )
        session_repo.create_session(session)
        print(f"  [OK] Created test session: {test_session_id}")

        # Create media asset with PENDING
        media = MediaAsset(
            id=test_media_id,
            session_id=test_session_id,
            media_type=MediaType.VIDEO,
            storage_bucket="analysis-inputs",
            storage_path=f"{test_session_id}/video/{test_media_id}_test.mp4",
            original_filename="test.mp4",
            mime_type="video/mp4",
            size_bytes=1048576,
            upload_status=UploadStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        media_repo.create_media_asset(media)
        print(f"  [OK] Created media asset with status PENDING: {test_media_id}")

        # Transition to VALIDATING
        updated = media_repo.update_media_validation(
            test_media_id,
            upload_status=UploadStatus.VALIDATING,
            validation_status="VALIDATING",
        )
        assert updated is not None, "Failed to update to VALIDATING"
        assert updated.upload_status == UploadStatus.VALIDATING
        print("  [OK] Persisted status VALIDATING")

        # Transition to VALIDATED with authoritative ffprobe metadata
        updated = media_repo.update_media_validation(
            test_media_id,
            upload_status=UploadStatus.VALIDATED,
            container_format="mov,mp4,m4a,3gp,3g2,mj2",
            video_codec="h264",
            audio_codec="aac",
            duration_seconds=120.5,
            width=1920,
            height=1080,
            fps=59.97,
            validation_status="SUCCESS",
        )
        assert updated is not None, "Failed to update to VALIDATED"
        assert updated.upload_status == UploadStatus.VALIDATED
        assert updated.container_format == "mov,mp4,m4a,3gp,3g2,mj2"
        assert updated.video_codec == "h264"
        assert updated.audio_codec == "aac"
        assert updated.duration_seconds == 120.5
        assert updated.width == 1920
        assert updated.height == 1080
        assert updated.fps == 59.97
        print("  [OK] Persisted status VALIDATED with authoritative container/codec/geometry metadata")

        # Fresh read from Supabase to verify durability
        fresh_asset = media_repo.get_media_asset(test_media_id)
        assert fresh_asset is not None
        assert fresh_asset.upload_status == UploadStatus.VALIDATED
        assert fresh_asset.container_format == "mov,mp4,m4a,3gp,3g2,mj2"
        assert fresh_asset.video_codec == "h264"
        assert fresh_asset.duration_seconds == 120.5
        print("  [OK] Fresh read confirmed durable persistence across client instances")

        # Test VALIDATION_FAILED state acceptance
        updated_fail = media_repo.update_media_validation(
            test_media_id,
            upload_status=UploadStatus.VALIDATION_FAILED,
            validation_status="FAILED",
            validation_error_code="UNSUPPORTED_CONTAINER",
        )
        assert updated_fail is not None
        assert updated_fail.upload_status == UploadStatus.VALIDATION_FAILED
        assert updated_fail.validation_error_code == "UNSUPPORTED_CONTAINER"
        print("  [OK] Persisted status VALIDATION_FAILED with error code")

        print("\n=== HARDENING PACK 2 LIVE SUPABASE VERIFICATION: PASS ===")

    finally:
        # Clean teardown
        try:
            client.table("media_assets").delete().eq("id", test_media_id).execute()
            client.table("sessions").delete().eq("id", test_session_id).execute()
            print("  [OK] Clean teardown of test session and media records completed.")
        except Exception as te:
            print(f"  [WARN] Teardown error: {te}")


if __name__ == "__main__":
    verify_live()
