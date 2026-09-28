"""
Regression and validation tests for golden showcase fixtures, media resolution,
and schema compatibility.
Uses real copied fixtures without mocking.
"""

import os
import json
import hashlib
import pytest

from backend.app.services.golden import GoldenFixtureService
from backend.app.schemas.showcase import (
    ShowcaseFrontendPayload,
    ShowcaseResponse,
    ShowcaseCard,
)


@pytest.fixture
def service():
    return GoldenFixtureService()


def test_a_manifest_parsing(service):
    """A. Test golden manifest parses and contains required top-level metadata."""
    manifest = service.load_manifest()
    assert manifest["manifest_version"] == "2.0"
    assert "artifacts" in manifest
    assert "media" in manifest
    assert "scientific_status" in manifest
    assert "mode" in manifest


def test_b_required_showcase_payload_availability(service):
    """B. Test required showcase payload files exist on disk."""
    fixtures_dir = service.fixtures_dir
    expected_files = [
        "showcase_frontend_payload.json",
        "showcase_final_coach_report.md",
        "showcase_grounding_validation.json",
        "showcase_final_summary.json",
    ]
    for filename in expected_files:
        path = os.path.join(fixtures_dir, filename)
        assert os.path.isfile(path), f"Missing required fixture: {filename}"
        assert os.path.getsize(path) > 0, f"Fixture is empty: {filename}"


def test_c_c03_c04_c06_presence(service):
    """C. Test C03, C04, and C06 media assets exist on disk with valid sizes."""
    manifest = service.load_manifest()
    media_entries = manifest["media"]

    assert "C06" in media_entries
    assert "C04" in media_entries
    assert "C03" in media_entries

    for case_id in ["C06", "C04", "C03"]:
        entry = media_entries[case_id]
        full_path = os.path.join(service.workspace_dir, entry["fixture_path"])
        assert os.path.isfile(full_path), f"Media file missing on disk for {case_id}: {full_path}"
        assert os.path.getsize(full_path) == entry["file_size_bytes"]


def test_d_media_map_resolution(service):
    """D. Test media map resolves original payload references to local fixtures."""
    media_map = service.load_media_map()
    assert "cases" in media_map
    cases = media_map["cases"]

    for case_id in ["C06", "C04", "C03"]:
        assert case_id in cases
        case_info = cases[case_id]
        assert case_info["resolution_status"] == "RESOLVED"
        assert os.path.isfile(os.path.join(service.workspace_dir, case_info["fixture_path"]))

        # Verify service resolution helper
        resolved = service.resolve_media(case_id)
        assert resolved is not None
        assert resolved.use_case == case_id
        assert resolved.sha256 == case_info["sha256"]


def test_e_checksum_consistency(service):
    """E. Test checksum consistency between recorded manifest hashes and actual file bytes."""
    integrity = service.verify_fixtures_integrity()
    for name, matches in integrity.items():
        assert matches is True, f"Checksum verification failed for {name}"


def test_f_showcase_status_exact_match(service):
    """F. Test showcase status strictly equals PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE."""
    manifest = service.load_manifest()
    assert manifest["scientific_status"] == "PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE"

    response = service.get_showcase_response()
    assert response.showcase_status == "PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE"


def test_g_showcase_mode_exact_match(service):
    """G. Test showcase mode strictly equals ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION."""
    manifest = service.load_manifest()
    assert manifest["mode"] == "ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION"

    payload = service.load_frontend_payload()
    assert payload.showcase_mode == "ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION"

    response = service.get_showcase_response()
    assert response.showcase_mode == "ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION"


def test_h_no_automated_identity_success_claim(service):
    """
    H. Test that no golden artifact claims automated persistent identity succeeded.
    Definitive automated status must remain FAIL_HIGH_FRAGMENTATION.
    """
    manifest = service.load_manifest()
    assert manifest["automated_identity_status"] == "FAIL_HIGH_FRAGMENTATION"

    payload = service.load_frontend_payload()
    assert payload.scientific_automated_status == "FAIL_HIGH_FRAGMENTATION"
    assert "AUTOMATED IDENTITY FAILED" in payload.badges

    response = service.get_showcase_response()
    assert response.scientific_automated_status == "FAIL_HIGH_FRAGMENTATION"
    assert "FAIL_HIGH_FRAGMENTATION" in response.disclaimer


def test_i_fixtures_not_modified_by_loader(service):
    """I. Test that loading fixtures does not modify the underlying files on disk."""
    payload_path = os.path.join(service.fixtures_dir, "showcase_frontend_payload.json")
    with open(payload_path, "rb") as f:
        before_hash = hashlib.sha256(f.read()).hexdigest()

    # Perform multiple load operations
    _ = service.load_frontend_payload()
    _ = service.get_showcase_response()
    _ = service.load_manifest()
    _ = service.load_media_map()

    with open(payload_path, "rb") as f:
        after_hash = hashlib.sha256(f.read()).hexdigest()

    assert before_hash == after_hash, "Golden fixture was modified during loader invocation!"


def test_j_typed_schema_compatibility(service):
    """J. Test typed showcase schema accurately parses the actual frozen payload."""
    payload = service.load_frontend_payload()
    assert isinstance(payload, ShowcaseFrontendPayload)
    assert len(payload.cards) == 3

    card_ids = [c.id for c in payload.cards]
    assert "C06_PRESSING" in card_ids
    assert "C04_DEFENSIVE_MARKING" in card_ids
    assert "C03_HOLD_POSITION" in card_ids

    # Verify response schema object serialization
    response = service.get_showcase_response()
    assert isinstance(response, ShowcaseResponse)
    assert len(response.cards) == 3
    assert len(response.resolved_media) == 3
    assert response.homography_rmse.value == 0.651
    assert response.homography_rmse.unit == "m"
