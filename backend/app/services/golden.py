"""
Service for loading and resolving frozen golden showcase fixtures and media.
This service is strictly read-only: it never modifies fixtures and never runs model inference.
"""

from __future__ import annotations
import os
import json
import hashlib
from typing import Dict, Any, Optional

from backend.app.schemas.showcase import (
    ShowcaseFrontendPayload,
    ShowcaseResponse,
    ShowcaseResolvedMedia,
)


class GoldenFixtureService:
    """
    Service responsible for loading immutable golden showcase fixtures and resolving
    media references through the media_map abstraction.
    """

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            # Default to root of the application workspace
            # golden.py is at backend/app/services/golden.py -> 3 levels up to workspace root
            self.workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        else:
            self.workspace_dir = os.path.abspath(base_dir)

        self.golden_dir = os.path.join(self.workspace_dir, "golden")
        self.fixtures_dir = os.path.join(self.golden_dir, "fixtures")
        self.manifest_path = os.path.join(self.golden_dir, "manifest.json")
        self.media_map_path = os.path.join(self.golden_dir, "media_map.json")

    def load_manifest(self) -> Dict[str, Any]:
        """Loads and parses golden/manifest.json."""
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_media_map(self) -> Dict[str, Any]:
        """Loads and parses golden/media_map.json."""
        with open(self.media_map_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_frontend_payload(self) -> ShowcaseFrontendPayload:
        """
        Loads and validates golden/fixtures/showcase_frontend_payload.json
        into a typed ShowcaseFrontendPayload schema.
        """
        payload_file = os.path.join(self.fixtures_dir, "showcase_frontend_payload.json")
        with open(payload_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return ShowcaseFrontendPayload(**raw_data)

    def load_coach_report(self) -> str:
        """Loads golden/fixtures/showcase_final_coach_report.md."""
        report_file = os.path.join(self.fixtures_dir, "showcase_final_coach_report.md")
        with open(report_file, "r", encoding="utf-8") as f:
            return f.read()

    def load_grounding_validation(self) -> Dict[str, Any]:
        """Loads golden/fixtures/showcase_grounding_validation.json."""
        val_file = os.path.join(self.fixtures_dir, "showcase_grounding_validation.json")
        with open(val_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_final_summary(self) -> Dict[str, Any]:
        """Loads golden/fixtures/showcase_final_summary.json."""
        summary_file = os.path.join(self.fixtures_dir, "showcase_final_summary.json")
        with open(summary_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def resolve_media(self, use_case: str) -> Optional[ShowcaseResolvedMedia]:
        """
        Resolves media for a specific showcase use case ('C03', 'C04', 'C06')
        using the application media map.
        """
        media_map = self.load_media_map()
        case_data = media_map.get("cases", {}).get(use_case)
        if not case_data:
            return None

        return ShowcaseResolvedMedia(
            logical_key=case_data["logical_key"],
            card_id=case_data["card_id"],
            use_case=case_data["use_case"],
            title=case_data["title"],
            fixture_path=case_data["fixture_path"],
            media_type=case_data["media_type"],
            file_size_bytes=case_data["file_size_bytes"],
            sha256=case_data["sha256"],
            storage_key=case_data.get("future_storage_key"),
        )

    def get_resolved_media_map(self) -> Dict[str, ShowcaseResolvedMedia]:
        """Returns all resolved media mapped by use case ID."""
        media_map = self.load_media_map()
        result = {}
        for case, data in media_map.get("cases", {}).items():
            result[case] = ShowcaseResolvedMedia(
                logical_key=data["logical_key"],
                card_id=data["card_id"],
                use_case=data["use_case"],
                title=data["title"],
                fixture_path=data["fixture_path"],
                media_type=data["media_type"],
                file_size_bytes=data["file_size_bytes"],
                sha256=data["sha256"],
                storage_key=data.get("future_storage_key"),
            )
        return result

    def verify_media_integrity(self, use_case: str) -> bool:
        """Check one local media file against its frozen manifest before serving it."""
        media = self.resolve_media(use_case)
        if media is None:
            return False
        path = os.path.join(self.workspace_dir, media.fixture_path)
        if not os.path.isfile(path) or os.path.getsize(path) != media.file_size_bytes:
            return False
        hasher = hashlib.sha256()
        with open(path, "rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest() == media.sha256

    def verify_fixtures_integrity(self) -> Dict[str, bool]:
        """
        Verifies that all fixture files and media exist on disk and match their recorded SHA-256 checksums.
        """
        manifest = self.load_manifest()
        results = {}

        # 1. Verify JSON/Markdown artifacts
        for name, entry in manifest.get("artifacts", {}).items():
            fixture_path = os.path.join(self.workspace_dir, entry["fixture_path"])
            if not os.path.exists(fixture_path):
                results[name] = False
                continue
            h = hashlib.sha256()
            with open(fixture_path, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            results[name] = (h.hexdigest() == entry["sha256"])

        # 2. Verify Media artifacts
        for case, entry in manifest.get("media", {}).items():
            fixture_path = os.path.join(self.workspace_dir, entry["fixture_path"])
            if not os.path.exists(fixture_path):
                results[f"media_{case}"] = False
                continue
            h = hashlib.sha256()
            with open(fixture_path, "rb") as f:
                while chunk := f.read(65536 * 16):
                    h.update(chunk)
            results[f"media_{case}"] = (h.hexdigest() == entry["sha256"])

        return results

    def get_showcase_response(self) -> ShowcaseResponse:
        """
        Constructs a complete, validated ShowcaseResponse object suitable for GET /showcase.
        Includes disclaimers, resolved media references, cards, and coach report.
        """
        payload = self.load_frontend_payload()
        manifest = self.load_manifest()
        resolved_media = self.get_resolved_media_map()

        disclaimer = (
            "Player identity and coach-instruction targets were manually verified for this capability demonstration. "
            "Automated persistent identity is evaluated separately and remains FAIL_HIGH_FRAGMENTATION. "
            "Metre-based values are approximate measured metric estimates (independent RMSE 0.651 m)."
        )

        return ShowcaseResponse(
            showcase_status=manifest.get("scientific_status", "PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE"),
            showcase_mode=payload.showcase_mode,
            scientific_automated_status=payload.scientific_automated_status,
            disclaimer=disclaimer,
            badges=payload.badges,
            cards=payload.cards,
            resolved_media=resolved_media,
            full_coach_report_markdown=payload.full_coach_report_markdown,
            limitations=payload.limitations,
            methodology_note=payload.methodology_note,
            homography_rmse=payload.homography_rmse,
        )


# Global default instance
golden_service = GoldenFixtureService()
