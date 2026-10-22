from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"chavi_recovery_phase1_forensic_audit_20260916"

def test_required_outputs_exist():
    names=["RECOVERY_PHASE1_FORENSIC_AUDIT_REPORT.md","workspace_directory_inventory.csv","artifact_inventory_with_hashes.csv","artifact_duplicate_and_conflict_map.csv","script_and_output_lineage.csv","code_lineage_and_independence_review.md","contract_and_approval_lineage.csv","contract_field_comparison.csv","stable_upstream_counts_reproduction.csv","reference_a_participant_manifest.csv","reference_a_fold_expected_counts.csv","reference_a_implementation_comparison.csv","transformed_artifact_variant_comparison.csv","wide_table_row_discrepancy_analysis.csv","extrapolation_count_reconciliation.csv","transformation_formula_comparison.csv","validation_independence_classification.csv","test_coverage_and_quality_matrix.csv","MASTER_ISSUE_REGISTER.csv","trusted_boundary_and_recovery_recommendation.md","recovery_phase1_claims_register.csv","recovery_phase1_provenance.json","recovery_phase1_audit.py","test_recovery_phase1_audit.py"]
    assert all((OUT/n).exists() for n in names)

def test_reference_a_reconstruction():
    rows=list(csv.DictReader((OUT/"reference_a_participant_manifest.csv").open(encoding="utf-8")))
    assert len({r["participant_id"] for r in rows})==109
    assert len(rows)==545

def test_no_existing_artifact_changed():
    p=json.loads((OUT/"recovery_phase1_provenance.json").read_text(encoding="utf-8"))
    assert p["existing_artifacts_changed"]==0
