"""Validate, inventory, and ZIP the corrected CHAVI preflight milestone."""
from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path


OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
MANIFEST = OUT / "milestone_artifact_manifest.csv"
ZIP_PATH = ROOT / f"{OUT.name}.zip"
REQUIRED = {
    "CORRECTED_PREFLIGHT_AND_DECISION_REVIEW.md",
    "crossfit_design_and_implementation_comparison.csv",
    "crossfit_candidate_identity_maps.csv",
    "corrected_source_cohort_reconciliation.csv",
    "reference_a_source_rows.csv",
    "primary_vf_source_rows.csv",
    "vonly_source_rows.csv",
    "qc_pairing_sensitivity_identity_comparison.csv",
    "contract_decision_register_corrected.csv",
    "step5ba_rebuild_specification_recommended.json",
    "transformation_output_schema.json",
    "bootstrap_protocol_and_limitations.md",
    "independent_validation_plan_corrected.md",
    "readiness_verdict_corrected.json",
    "CONTRACT_REVIEW_AND_APPROVAL_TEMPLATE.md",
    "historical_artifact_before_after_hashes.csv",
    "provenance_and_reproduction.md",
    "reconstruct_and_audit.py",
    "test_corrected_preflight.py",
    "finalize_package.py",
}
FORBIDDEN = {"transformation_parameters.csv", "transformed_task_observations_long.csv", "transformed_profiles_wide.csv"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    available = {p.name for p in OUT.iterdir() if p.is_file()}
    missing = REQUIRED - available
    if missing:
        raise AssertionError(f"missing required artifacts: {sorted(missing)}")
    if FORBIDDEN & available:
        raise AssertionError(f"production outputs present: {sorted(FORBIDDEN & available)}")
    row_counts = {}
    for path in sorted(OUT.glob("*.csv")):
        if path == MANIFEST:
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            row_counts[path.name] = len(list(csv.DictReader(handle)))
    for path in sorted(OUT.glob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))
    expected = {"reference_a_source_rows.csv":545, "primary_vf_source_rows.csv":520,
                "vonly_source_rows.csv":450, "corrected_source_cohort_reconciliation.csv":132,
                "crossfit_candidate_identity_maps.csv":15}
    for name, count in expected.items():
        if row_counts.get(name) != count:
            raise AssertionError(f"{name} expected {count}, got {row_counts.get(name)}")
    files = sorted(p for p in OUT.iterdir() if p.is_file() and p != MANIFEST and p.suffix != ".pyc")
    rows = [{"relative_path":p.name, "size_bytes":p.stat().st_size, "sha256":sha256(p),
             "csv_data_rows":row_counts.get(p.name, ""), "included_in_zip":"yes"} for p in files]
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    package_files = sorted(p for p in OUT.iterdir() if p.is_file() and p.suffix != ".pyc")
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in package_files:
            archive.write(path, arcname=f"{OUT.name}/{path.name}")
    print(json.dumps({"artifact_files_in_zip":len(package_files), "csv_row_counts":row_counts,
                      "zip_path":str(ZIP_PATH), "zip_size_bytes":ZIP_PATH.stat().st_size,
                      "zip_sha256":sha256(ZIP_PATH)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
