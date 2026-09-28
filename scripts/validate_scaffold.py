#!/usr/bin/env python3
"""
Scaffold and Contract Validation Script.
Validates repository structure, YAML/JSON parsing, schema imports,
absence of secrets, absence of prohibited hardcoded paths in runtime code,
and adherence to scientific boundaries.
"""

import os
import sys
import json
import re

# Ensure base_dir is on sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

try:
    import yaml
except ImportError:
    yaml = None


def run_checks():
    errors = []
    warnings = []

    print("=" * 60)
    print("1. CHECKING DIRECTORY STRUCTURE")
    print("=" * 60)
    expected_dirs = [
        "backend",
        os.path.join("backend", "app"),
        os.path.join("backend", "app", "api"),
        os.path.join("backend", "app", "core"),
        os.path.join("backend", "app", "schemas"),
        os.path.join("backend", "app", "services"),
        os.path.join("backend", "app", "pipeline"),
        os.path.join("backend", "tests"),
        "frontend",
        "modal_app",
        "shared",
        os.path.join("shared", "constants"),
        os.path.join("shared", "schemas"),
        "golden",
        "docs",
        os.path.join("docs", "research_handoff"),
        "scripts",
    ]
    for d in expected_dirs:
        p = os.path.join(base_dir, d)
        if os.path.isdir(p):
            print(f"  [OK] Directory exists: {d}")
        else:
            errors.append(f"Missing required directory: {d}")
            print(f"  [FAIL] Missing required directory: {d}")

    print("\n" + "=" * 60)
    print("2. CHECKING REQUIRED ROOT AND MANIFEST FILES")
    print("=" * 60)
    expected_files = [
        ".gitignore",
        ".env.example",
        "README.md",
        "AGENTS.md",
        os.path.join("docs", "architecture.md"),
        os.path.join("docs", "deployment_targets.md"),
        os.path.join("golden", "README.md"),
        os.path.join("golden", "manifest.json"),
        os.path.join("backend", "app", "core", "model_manifest.yaml"),
        os.path.join("backend", "requirements.txt"),
        os.path.join("backend", "pyproject.toml"),
    ]
    for f in expected_files:
        p = os.path.join(base_dir, f)
        if os.path.isfile(p):
            print(f"  [OK] File exists: {f}")
        else:
            errors.append(f"Missing required file: {f}")
            print(f"  [FAIL] Missing required file: {f}")

    print("\n" + "=" * 60)
    print("3. VALIDATING JSON AND YAML PARSING")
    print("=" * 60)
    # Check JSON files
    json_files = [
        os.path.join("golden", "manifest.json"),
        os.path.join("golden", "media_map.json"),
        os.path.join("golden", "fixtures", "showcase_frontend_payload.json"),
        os.path.join("golden", "fixtures", "showcase_grounding_validation.json"),
        os.path.join("golden", "fixtures", "showcase_final_summary.json"),
        os.path.join("docs", "research_handoff", "integration_audit.json"),
    ]
    for jf in json_files:
        p = os.path.join(base_dir, jf)
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    json.load(f)
                print(f"  [OK] JSON parsed successfully: {jf}")
            except Exception as e:
                errors.append(f"Failed to parse JSON {jf}: {e}")
                print(f"  [FAIL] JSON parse error in {jf}: {e}")

    # Check YAML files
    yaml_files = [
        os.path.join("backend", "app", "core", "model_manifest.yaml"),
    ]
    if yaml is not None:
        for yf in yaml_files:
            p = os.path.join(base_dir, yf)
            if os.path.isfile(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        yaml.safe_load(f)
                    print(f"  [OK] YAML parsed successfully: {yf}")
                except Exception as e:
                    errors.append(f"Failed to parse YAML {yf}: {e}")
                    print(f"  [FAIL] YAML parse error in {yf}: {e}")
    else:
        warnings.append("PyYAML not installed; skipped YAML parsing verification.")

    print("\n" + "=" * 60)
    print("4. CHECKING PYTHON SCHEMAS AND IMPORTS")
    print("=" * 60)
    try:
        import backend.app.schemas as s
        symbols = s.__all__
        print(f"  [OK] backend.app.schemas imported successfully ({len(symbols)} symbols)")
    except Exception as e:
        errors.append(f"Failed to import backend.app.schemas: {e}")
        print(f"  [FAIL] Import failed for backend.app.schemas: {e}")

    print("\n" + "=" * 60)
    print("5. VERIFYING SECRETS HYGIENE IN REPOSITORY")
    print("=" * 60)
    secret_patterns = [
        re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
        re.compile(r"eyJhbGciOi[a-zA-Z0-9_\-\.]{50,}", re.IGNORECASE),
        re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE),
    ]
    suspicious_found = False
    for root, dirs, files in os.walk(base_dir):
        if ".git" in root or "__pycache__" in root or "node_modules" in root:
            continue
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith((".py", ".ts", ".tsx", ".md", ".json", ".yaml", ".yml", ".txt")):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pat in secret_patterns:
                        if pat.search(content):
                            errors.append(f"Potential real secret pattern matched in {filepath}")
                            print(f"  [FAIL] Secret detected in: {filepath}")
                            suspicious_found = True
    if not suspicious_found:
        print("  [OK] No live secrets or API key patterns detected.")

    print("\n" + "=" * 60)
    print("6. VERIFYING RUNTIME CODE PATH HYGIENE")
    print("=" * 60)
    # Production runtime code (backend/app/pipeline, backend/app/schemas, shared) must NOT depend on /content/drive or D:\ paths
    runtime_dirs = [
        os.path.join("backend", "app", "pipeline"),
        os.path.join("backend", "app", "schemas"),
        os.path.join("shared"),
    ]
    path_violation_found = False
    for rd in runtime_dirs:
        full_rd = os.path.join(base_dir, rd)
        for root, dirs, files in os.walk(full_rd):
            if "__pycache__" in root or "node_modules" in root:
                continue
            for file in files:
                if not file.endswith((".py", ".ts")):
                    continue
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        stripped = line.strip()
                        # Allow comments/docstrings referencing historical provenance
                        if stripped.startswith(("#", "//", "*", '"""', "'''")):
                            continue
                        if "/content/drive" in line or "D:\\" in line or "C:\\" in line:
                            errors.append(f"Hardcoded environment path in executable runtime code at {filepath}:{i+1}")
                            print(f"  [FAIL] Path violation at {filepath}:{i+1}")
                            path_violation_found = True
    if not path_violation_found:
        print("  [OK] No executable runtime code depends on /content/drive or Windows paths.")

    print("\n" + "=" * 60)
    print("7. VERIFYING SCIENTIFIC BOUNDARIES & DEPLOYMENT DECISION")
    print("=" * 60)
    agents_path = os.path.join(base_dir, "AGENTS.md")
    with open(agents_path, "r", encoding="utf-8") as f:
        agents_content = f.read()

    if "FAIL_HIGH_FRAGMENTATION" in agents_content:
        print("  [OK] Persistent identity failure (FAIL_HIGH_FRAGMENTATION) recorded.")
    else:
        errors.append("AGENTS.md missing explicit FAIL_HIGH_FRAGMENTATION boundary.")

    if "Stage 4B fine-tuned YOLO11m" in agents_content and "SELECTED_FOR_DEPLOYMENT" in agents_content:
        print("  [OK] Deployment detector (Stage 4B fine-tuned YOLO11m) explicitly recorded.")
    else:
        errors.append("AGENTS.md missing explicit Stage 4B fine-tuned YOLO11m deployment detector record.")

    if "PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE" in agents_content:
        print("  [OK] Showcase status PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE recorded.")
    else:
        errors.append("AGENTS.md missing showcase status record.")

    print("\n" + "=" * 60)
    print("8. VERIFYING RESEARCH PROVENANCE PRESERVATION")
    print("=" * 60)
    handoff_dir = os.path.join(base_dir, "docs", "research_handoff")
    handoff_files = [
        "integration_audit.json",
        "integration_audit.md",
        "integration_dependency_audit.md",
        "integration_file_map.csv",
        "integration_handoff_to_antigravity.md",
        "integration_runtime_risks.md",
    ]
    all_handoff_present = True
    for hf in handoff_files:
        hp = os.path.join(handoff_dir, hf)
        if not os.path.isfile(hp):
            errors.append(f"Research handoff file missing: {hf}")
            print(f"  [FAIL] Missing handoff file: {hf}")
            all_handoff_present = False
        else:
            print(f"  [OK] Handoff file preserved: {hf}")

    print("\n" + "=" * 60)
    print("9. VERIFYING GOLDEN FIXTURE INTEGRITY VIA SERVICE")
    print("=" * 60)
    try:
        from backend.app.services.golden import GoldenFixtureService
        service = GoldenFixtureService(base_dir)
        integrity = service.verify_fixtures_integrity()
        all_passed = True
        for artifact_name, matches in integrity.items():
            if matches:
                print(f"  [OK] Golden integrity verified: {artifact_name}")
            else:
                errors.append(f"Golden integrity check failed for: {artifact_name}")
                print(f"  [FAIL] Golden integrity check failed: {artifact_name}")
                all_passed = False
        resp = service.get_showcase_response()
        print(f"  [OK] ShowcaseResponse generated successfully with {len(resp.cards)} cards and {len(resp.resolved_media)} resolved media entries.")
    except Exception as e:
        errors.append(f"GoldenFixtureService execution error: {e}")
        print(f"  [FAIL] GoldenFixtureService error: {e}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Errors: {len(errors)}")
    print(f"Total Warnings: {len(warnings)}")
    for w in warnings:
        print(f"  Warning: {w}")
    for e in errors:
        print(f"  Error: {e}")

    if errors:
        print("\n>>> VALIDATION FAILED <<<")
        return 1
    else:
        print("\n>>> ALL VALIDATION CHECKS PASSED <<<")
        return 0


if __name__ == "__main__":
    sys.exit(run_checks())
