import os
import shutil
import hashlib
import sys

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    workspace = os.path.abspath(".")
    research_root = os.path.dirname(workspace)
    golden_dir = os.path.join(workspace, "golden")
    fixtures_dir = os.path.join(golden_dir, "fixtures")
    media_dir = os.path.join(golden_dir, "media")

    os.makedirs(fixtures_dir, exist_ok=True)
    os.makedirs(media_dir, exist_ok=True)

    print(f"Workspace: {workspace}", flush=True)
    print(f"Research Root: {research_root}", flush=True)

    # 1. Payload fixtures
    source_showcase_dir = os.path.join(research_root, "physical_metric_upgrade", "experiments", "capability_showcase", "05_final_showcase")
    payload_files = [
        "showcase_frontend_payload.json",
        "showcase_final_coach_report.md",
        "showcase_grounding_validation.json",
        "showcase_final_summary.json",
    ]

    for pf in payload_files:
        src = os.path.join(source_showcase_dir, pf)
        dst = os.path.join(fixtures_dir, pf)
        if not os.path.exists(src):
            print(f"ERROR: Source file does not exist: {src}", flush=True)
            return 1
        shutil.copy2(src, dst)
        h_src = sha256_file(src)
        h_dst = sha256_file(dst)
        assert h_src == h_dst, f"Checksum mismatch for {pf}"
        print(f"Copied fixture: {pf} ({os.path.getsize(dst)} bytes, sha256={h_dst})", flush=True)

    # 2. Media files
    media_targets = [
        ("C06", os.path.join(research_root, "C06_pressing_deterministic_response", "C06_pressing_sequence_overlay.mp4"), os.path.join(media_dir, "c06", "C06_pressing_sequence_overlay.mp4")),
        ("C04", os.path.join(research_root, "c04_deterministic_response", "C04_black01_red03_response_contact_sheet.png"), os.path.join(media_dir, "c04", "C04_black01_red03_response_contact_sheet.png")),
        ("C03", os.path.join(research_root, "C03_hold_position_deterministic_response", "C03_hold_position_overlay.mp4"), os.path.join(media_dir, "c03", "C03_hold_position_overlay.mp4")),
    ]

    for case, src, dst in media_targets:
        if not os.path.exists(src):
            print(f"ERROR: Source media does not exist: {src}", flush=True)
            return 1
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        print(f"Copying media for {case} from {src} to {dst} ...", flush=True)
        shutil.copy2(src, dst)
        h_src = sha256_file(src)
        h_dst = sha256_file(dst)
        assert h_src == h_dst, f"Checksum mismatch for {case}"
        print(f"Copied media {case}: {os.path.basename(dst)} ({os.path.getsize(dst)} bytes, sha256={h_dst})", flush=True)

    print("All fixtures and media copied and checksum-verified successfully!", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
