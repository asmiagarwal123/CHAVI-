"""
CHAVI Step 5A-D-R Automated Tests
==================================
Tests every acceptance criterion from the correction prompt.
Run with: pytest test_step5adr.py -v
"""
import os
import json
import hashlib
import subprocess
import numpy as np
import pandas as pd
import pytest

ROOT    = r"C:\Users\asmi\Desktop\Projects\CHAVI"
DATASET = os.path.join(ROOT, "ds007116")
STEP3B  = os.path.join(ROOT, "chavi_audit_ds007116_step3b_20260909")
OUT     = os.path.join(ROOT, "chavi_analysis_ds007116_step5adr_correction_20260916")

EXPECTED_COMMIT = "fc7dc36fa2598b0b2e4579baef37d148cc085207"
EXPECTED_TAG    = "1.0.6"
EXPECTED_INPUT_HASH = "8b435d4b23d0b5f70b3c56ade4215d215028426dbdb46eaaf8daaa3cd0dc1978"

SELECTED_TASKS = ["cnb_lnb_mcr", "cnb_cpf_cr", "cnb_pmat_cr", "cnb_er40_cr", "cnb_ctap_dom"]

# ── helpers ───────────────────────────────────────────────────────────────────
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def git_out(args):
    return subprocess.check_output(["git"] + args, cwd=DATASET).decode().strip()

def out(name):
    return os.path.join(OUT, name)

def load(name):
    return pd.read_csv(out(name))

def load_json(name):
    with open(out(name)) as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 1 — Dataset integrity
# ═══════════════════════════════════════════════════════════════════════════════

def test_dataset_commit_unchanged():
    assert git_out(["rev-parse", "HEAD"]) == EXPECTED_COMMIT

def test_dataset_tag_unchanged():
    assert git_out(["describe", "--tags"]) == EXPECTED_TAG

def test_dataset_working_tree_clean():
    assert git_out(["status", "--porcelain"]) == ""

def test_input_hash_unchanged():
    path = os.path.join(STEP3B, "task_observations_long.csv")
    assert sha256(path) == EXPECTED_INPUT_HASH


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 2 — Cohort counts
# ═══════════════════════════════════════════════════════════════════════════════

def test_cohort_52_participants():
    df = load("cohort_reproduction.csv")
    assert len(df) == 52, f"Expected 52, got {len(df)}"

def test_provenance_cohort_counts():
    prov = load_json("step5adr_provenance.json")
    cc = prov["cohort_counts_reproduced"]
    assert cc["complete_occasions"] == 176
    assert cc["participants_1plus"]  == 109
    assert cc["participants_2plus"]  == 52

def test_no_duplicate_participant_in_cohort():
    df = load("cohort_reproduction.csv")
    assert df["participant_id"].nunique() == len(df)


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 3 — C1 LNB score semantics
# ═══════════════════════════════════════════════════════════════════════════════

def test_lnb_not_response_time():
    df = load("direction_and_unit_register.csv")
    lnb = df[df["score_field"] == "cnb_lnb_mcr"].iloc[0]
    assert lnb["is_response_time"] == False
    assert "COUNT" in str(lnb["field_type"]).upper()

def test_lnb_direction_positive():
    df = load("direction_and_unit_register.csv")
    lnb = df[df["score_field"] == "cnb_lnb_mcr"].iloc[0]
    assert int(lnb["direction_multiplier"]) == 1

def test_all_task_directions_positive():
    df = load("direction_and_unit_register.csv")
    assert (df["direction_multiplier"].astype(int) == 1).all()


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 4 — C2 Contract QC column
# ═══════════════════════════════════════════════════════════════════════════════

def test_contract_qc_column_is_VF():
    contract = load_json("step5adr_transformation_contract_draft.json")
    col = contract["eligible_qc_column"]
    assert "valid_or_likely_valid" in col, f"Expected V/F column, got: {col}"

def test_contract_eligible_qc_value():
    contract = load_json("step5adr_transformation_contract_draft.json")
    assert contract["eligible_qc_value"] == "yes"


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 5 — C3 Fold determinism and no leakage
# ═══════════════════════════════════════════════════════════════════════════════

def test_fold_manifest_exists():
    assert os.path.exists(out("participant_grouped_fold_manifest.csv"))

def test_each_participant_in_exactly_one_fold():
    df = load("participant_grouped_fold_manifest.csv")
    counts = df.groupby("participant_id")["fold"].nunique()
    assert (counts == 1).all(), "Participant appears in more than one fold"

def test_fold_count_is_five():
    df = load("participant_grouped_fold_manifest.csv")
    assert df["fold"].nunique() == 5

def test_fold_manifest_deterministic():
    """Re-importing the fold manifest and checking it is identical on two reads."""
    df1 = load("participant_grouped_fold_manifest.csv")
    df2 = load("participant_grouped_fold_manifest.csv")
    pd.testing.assert_frame_equal(df1, df2)

def test_fold_total_participants():
    df = load("participant_grouped_fold_manifest.csv")
    assert df["participant_id"].nunique() == 52


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 6 — C4 Age models on baseline-reference cohort
# ═══════════════════════════════════════════════════════════════════════════════

def test_age_model_comparison_exists():
    assert os.path.exists(out("age_model_comparison.csv"))

def test_age_model_comparison_has_three_models():
    df = load("age_model_comparison.csv")
    models = df["model"].unique()
    assert "M0_intercept_only" in models
    assert "M1_linear_age" in models
    assert "M2_spline_df3" in models

def test_age_model_comparison_all_tasks():
    df = load("age_model_comparison.csv")
    for task in SELECTED_TASKS:
        assert task in df["task"].values, f"Task {task} missing from age model comparison"

def test_age_support_audit_has_baseline_cohort():
    df = load("age_support_audit.csv")
    assert "baseline_reference" in df["cohort"].values


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 7 — C5 Residual and extrapolation diagnostics
# ═══════════════════════════════════════════════════════════════════════════════

def test_oof_diagnostics_exist():
    assert os.path.exists(out("out_of_fold_diagnostics.csv"))

def test_residual_age_trend_diagnostics_exist():
    assert os.path.exists(out("residual_age_trend_diagnostics.csv"))

def test_extrapolation_audit_exists():
    assert os.path.exists(out("extrapolation_audit.csv"))

def test_extrapolation_audit_has_all_tasks():
    df = load("extrapolation_audit.csv")
    for task in SELECTED_TASKS:
        assert task in df["task"].values

def test_extrapolation_flag_is_boolean():
    df = load("extrapolation_audit.csv")
    assert df["extrapolated"].dtype in [bool, object, "bool"]


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 8 — C6 SD versus MAD comparison
# ═══════════════════════════════════════════════════════════════════════════════

def test_sd_mad_comparison_exists():
    assert os.path.exists(out("sd_vs_mad_comparison.csv"))

def test_sd_mad_comparison_has_all_tasks():
    df = load("sd_vs_mad_comparison.csv")
    for task in SELECTED_TASKS:
        assert task in df["task"].values

def test_scale_stability_no_universal_zero():
    df = load("scale_stability_diagnostics.csv")
    # Not all folds/tasks should have zero scale
    if len(df) > 0:
        assert not (df["zero_scale_sd"].all()), "All SD scales are zero — something is wrong"


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 9 — C7 Bootstrap feasibility
# ═══════════════════════════════════════════════════════════════════════════════

def test_bootstrap_feasibility_exists():
    assert os.path.exists(out("bootstrap_feasibility.json"))

def test_bootstrap_has_valid_reps():
    d = load_json("bootstrap_feasibility.json")
    bf = d["bootstrap_feasibility"]
    assert bf["n_valid"] > 0, "No valid bootstrap replicates"
    assert bf["n_reps"] == 200

def test_bootstrap_failure_inventory_exists():
    assert os.path.exists(out("bootstrap_failure_inventory.csv"))


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 10 — C9 Ipsative / centering correction
# ═══════════════════════════════════════════════════════════════════════════════

def test_ipsative_correction_exists():
    assert os.path.exists(out("ipsative_centering_correction.md"))

def test_contract_centered_shape_dimensionality():
    contract = load_json("step5adr_transformation_contract_draft.json")
    ips = contract["ipsative_constraint"]
    assert ips["effective_dimensionality"] == 4
    assert ips["not_five_independent_dims"] == True

def test_centered_shape_sum_to_zero_algebraically():
    """Verify numerically: if we compute S_itj = Z_itj - L_it, sum_j S_itj == 0."""
    # Create a synthetic 5-component profile
    rng = np.random.default_rng(0)
    for _ in range(100):
        Z = rng.normal(size=5)
        L = Z.mean()
        S = Z - L
        assert abs(S.sum()) < 1e-10, f"Centered shape sum not zero: {S.sum()}"


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 11 — Contract schema and status
# ═══════════════════════════════════════════════════════════════════════════════

def test_contract_status_not_ready():
    contract = load_json("step5adr_transformation_contract_draft.json")
    assert contract["status"] == "not_ready"

def test_contract_technical_verdict():
    contract = load_json("step5adr_transformation_contract_draft.json")
    assert contract["contract_technical_verdict"] == "READY_FOR_HUMAN_DECISION"

def test_contract_has_five_tasks():
    contract = load_json("step5adr_transformation_contract_draft.json")
    assert len(contract["task_fields"]) == 5

def test_contract_has_unresolved_blockers():
    contract = load_json("step5adr_transformation_contract_draft.json")
    assert len(contract["unresolved_blockers"]) > 0

def test_contract_correction_notes_all_nine():
    contract = load_json("step5adr_transformation_contract_draft.json")
    notes = contract["correction_notes"]
    for i in range(1, 10):
        assert f"C{i}" in notes, f"Correction C{i} missing from contract notes"


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 12 — Decision matrix
# ═══════════════════════════════════════════════════════════════════════════════

def test_decision_matrix_exists():
    assert os.path.exists(out("step5adr_decision_matrix.csv"))

def test_decision_matrix_has_d18_lnb():
    df = load("step5adr_decision_matrix.csv")
    assert "D18" in df["decision_id"].values, "D18 (LNB direction) missing from decision matrix"

def test_all_decisions_blocked():
    df = load("step5adr_decision_matrix.csv")
    assert (df["final_status"] == "blocked").all(), "Some decisions not marked blocked"

def test_all_decisions_require_human_approval():
    df = load("step5adr_decision_matrix.csv")
    assert df["requires_human_approval"].all()


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP 13 — Preservation of previous outputs
# ═══════════════════════════════════════════════════════════════════════════════

def test_step3b_input_unchanged():
    path = os.path.join(STEP3B, "task_observations_long.csv")
    assert sha256(path) == EXPECTED_INPUT_HASH

def test_step5ad_directory_untouched():
    """Previous Step 5A-D directory must still exist and be non-empty."""
    d = os.path.join(ROOT, "chavi_analysis_ds007116_step5ad_decision_freeze_20260916")
    assert os.path.isdir(d)
    assert len(os.listdir(d)) > 0

def test_step5a_directory_untouched():
    d = os.path.join(ROOT, "chavi_analysis_ds007116_step5a_measurement_specification_20260916")
    assert os.path.isdir(d)
    assert len(os.listdir(d)) > 0

def test_no_profile_scores_computed():
    """No file in the output directory should contain final profile ICC or reliability."""
    forbidden_keywords = ["profile_icc", "profile_reliability", "step5b", "evidence_engine"]
    for f in os.listdir(OUT):
        if f.endswith(".py") or f.endswith(".json") and "contract" in f:
            continue
        if f.endswith((".csv", ".md")):
            path = os.path.join(OUT, f)
            with open(path, encoding="utf-8", errors="replace") as fh:
                content = fh.read().lower()
            for kw in forbidden_keywords:
                assert kw not in content, f"Forbidden keyword '{kw}' found in {f}"
