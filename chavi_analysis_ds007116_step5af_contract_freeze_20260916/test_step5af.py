"""
CHAVI Step 5A-F Contract Freeze Test Suite
==========================================
"""
import os, json, yaml, hashlib
import pytest

ROOT = r"C:\Users\asmi\Desktop\Projects\CHAVI"
R2 = os.path.join(ROOT, "chavi_analysis_ds007116_step5adr2_final_review_20260916")
OUT = os.path.join(ROOT, "chavi_analysis_ds007116_step5af_contract_freeze_20260916")

def test_supervisor_approval_exists():
    assert os.path.exists(os.path.join(OUT, "SUPERVISOR_APPROVAL.yaml"))

def test_frozen_contract_exists():
    assert os.path.exists(os.path.join(OUT, "step5af_transformation_contract_frozen.json"))

def test_18_decisions_recorded():
    with open(os.path.join(OUT, "SUPERVISOR_APPROVAL.yaml")) as f:
        doc = yaml.safe_load(f)
    decs = doc["supervisor_approval_record"]["decisions"]
    assert len(decs) == 18
    for i in range(1, 19):
        assert f"D{i}" in decs

def test_no_pending_or_tbd_values():
    with open(os.path.join(OUT, "SUPERVISOR_APPROVAL.yaml")) as f:
        text = f.read().lower()
    assert "pending" not in text
    assert "tbd" not in text
    assert "[" not in text or "]" not in text  # no brackets like [APPROVED VALUE]

def test_reference_a_109():
    with open(os.path.join(OUT, "step5af_transformation_contract_frozen.json")) as f:
        c = json.load(f)
    assert "109" in c["reference_cohort"]
    assert "Ref_A" in c["reference_cohort"]

def test_primary_cohort_52():
    with open(os.path.join(OUT, "step5af_transformation_contract_frozen.json")) as f:
        c = json.load(f)
    assert c["primary_cohort_count"] == 52

def test_v_only_sensitivity():
    with open(os.path.join(OUT, "SUPERVISOR_APPROVAL.yaml")) as f:
        doc = yaml.safe_load(f)
    assert "sensitivity" in str(doc["supervisor_approval_record"]["decisions"]["D3"]["approved_value"]).lower()

def test_no_age_primary():
    with open(os.path.join(OUT, "step5af_transformation_contract_frozen.json")) as f:
        c = json.load(f)
    assert "no age" in c["primary_coordinate"].lower()
    assert "M0_no_age_adjustment" == c["age_model_primary"]

def test_mad_primary_sd_sensitivity():
    with open(os.path.join(OUT, "step5af_transformation_contract_frozen.json")) as f:
        c = json.load(f)
    assert "MAD_primary" in c["scale_estimator_primary"]
    assert "SD_sensitivity" in c["scale_estimator_primary"]

def test_extrapolation_policy():
    with open(os.path.join(OUT, "step5af_transformation_contract_frozen.json")) as f:
        c = json.load(f)
    assert "P3" in c["extrapolation_policy"]
    assert "unsupported" in c["extrapolation_policy"].lower()
    assert "M0" in c["extrapolation_policy"]

def test_lnb_semantics():
    with open(os.path.join(OUT, "step5af_transformation_contract_frozen.json")) as f:
        c = json.load(f)
    assert c["task_direction_multipliers"]["cnb_lnb_mcr"] == 1
    assert "COUNT of true positive" in c["lnb_confirmed_type"]

def test_lnb_caveat_remains():
    with open(os.path.join(OUT, "step5af_transformation_contract_frozen.json")) as f:
        c = json.load(f)
    assert c["lnb_denominator_resolved"] == False

def test_previous_artifacts_unchanged():
    assert os.path.exists(R2)
    with open(os.path.join(R2, "step5adr2_transformation_contract_candidate.json")) as f:
        c2 = json.load(f)
    assert c2["status"] == "not_ready"

def test_no_profile_results_generated():
    forbidden = ["Z_score", "profile_icc"]
    for f_name in os.listdir(OUT):
        if f_name.endswith(".csv"):
            with open(os.path.join(OUT, f_name), encoding="utf-8") as f:
                content = f.read().lower()
                for keyword in forbidden:
                    assert keyword.lower() not in content
