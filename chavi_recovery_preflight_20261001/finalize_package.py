"""Validate and package the CHAVI recovery-preflight milestone."""
from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path


OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
ZIP_PATH = ROOT / f"{OUT.name}.zip"
MANIFEST = OUT / "milestone_artifact_manifest.csv"

REQUIRED = {
    "RECOVERY_PREFLIGHT_REPORT.md",
    "input_artifact_manifest.csv",
    "source_cohort_reconciliation.csv",
    "reference_cohort_manifest.csv",
    "participant_fold_manifest.csv",
    "contract_gap_and_decision_register.csv",
    "step5ba_rebuild_specification_candidate.json",
    "independent_validation_plan.md",
    "environment_and_reproduction.md",
    "readiness_verdict.json",
    "reconstruct_source_cohorts.py",
    "test_preflight.py",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    available = {p.name for p in OUT.iterdir() if p.is_file()}
    missing = sorted(REQUIRED - available)
    if missing:
        raise AssertionError(f"Missing required deliverables: {missing}")

    csv_counts: dict[str, int] = {}
    for path in sorted(OUT.glob("*.csv")):
        if path == MANIFEST:
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            csv_counts[path.name] = sum(1 for _ in csv.DictReader(handle))
    for path in sorted(OUT.glob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))

    files = sorted(
        p for p in OUT.iterdir()
        if p.is_file() and p != MANIFEST and p.suffix not in {".pyc"}
    )
    rows = []
    for path in files:
        rows.append({
            "relative_path": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "csv_data_rows": csv_counts.get(path.name, ""),
            "included_in_zip": "yes",
        })
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    package_files = sorted(
        p for p in OUT.iterdir()
        if p.is_file() and p.suffix not in {".pyc"}
    )
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in package_files:
            archive.write(path, arcname=f"{OUT.name}/{path.name}")

    print(json.dumps({
        "csv_row_counts": csv_counts,
        "package_file_count": len(package_files),
        "zip_path": str(ZIP_PATH),
        "zip_size_bytes": ZIP_PATH.stat().st_size,
        "zip_sha256": sha256(ZIP_PATH),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
