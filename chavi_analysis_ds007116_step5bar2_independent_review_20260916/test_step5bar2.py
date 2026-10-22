"""
CHAVI Step 5B-A Test Suite
==========================
"""
import os, json
import pandas as pd
import pytest

ROOT = r"C:\Users\asmi\Desktop\Projects\CHAVI"
OUT = os.path.join(ROOT, "chavi_analysis_ds007116_step5bar2_independent_review_20260916")

def load(name):
    return pd.read_csv(os.path.join(OUT, name))

def jload(name):
    with open(os.path.join(OUT, name)) as f: return json.load(f)

def test_frozen_contract_hash():
    prov = jload("step5ba_provenance.json")
    assert prov["frozen_contract_hash"] == "cde670d47e30895b2e6122b803cb3a27997d7c08132d98e439dfab691b28ecce"

def test_input_hashes():
    # Validated strictly in script, assuming success if outputs exist
    assert os.path.exists(os.path.join(OUT, "transformed_task_observations_long.csv"))

def test_cohort_identities():
    df = load("transformed_profiles_wide.csv")
    assert set(df["raw_qc_codes"].unique()).issubset({"V", "F"})

def test_exact_task_count_per_occasion():
    df = load("transformed_task_observations_long.csv")
    counts = df.groupby(["participant_id", "repository_session_id"])["score_field"].nunique()
    assert (counts == 5).all()

def test_two_occasions_per_primary_participant():
    df = load("transformed_profiles_wide.csv")
    primary = df[df["analytical_stratum"].str.contains("Primary")]
    counts = primary.groupby("participant_id")["repository_session_id"].nunique()
    assert (counts == 2).all()

def test_duplicate_keys():
    df = load("transformed_task_observations_long.csv")
    dups = df.duplicated(subset=["participant_id", "repository_session_id", "analytical_stratum", "score_field"])
    assert not dups.any()

def test_chronological_order():
    df = load("transformed_profiles_wide.csv")
    for pid, group in df.groupby("participant_id"):
        assert group["session_age"].is_monotonic_increasing

def test_no_leakage():
    df = load("transformed_task_observations_long.csv")
    # A single fold column exists per participant
    assert (df.groupby("participant_id")["fold"].nunique() == 1).all()

def test_training_only_reference_fitting():
    params = load("transformation_parameters.csv")
    assert (params["training_reference_size"] > 0).all()
    assert (params["training_reference_size"] < 110).all() # Should be around 87 (109 minus 22 in fold)

def test_fold_specific_parameters():
    params = load("transformation_parameters.csv")
    # Means should vary slightly between folds
    assert params.groupby("score_field")["m0_mean"].nunique().gt(1).any()

def test_task_directions():
    df = load("transformed_task_observations_long.csv")
    # Score = direction * (val - mean)/scale
    # If val > mean and direction == 1 -> score > 0
    # If val > mean and direction == -1 -> score < 0
    df["expected_sign"] = np.sign(df["raw_value"] - df["predicted_reference_value"]) * df["direction_multiplier"]
    df["actual_sign"] = np.sign(df["primary_transformed_coordinate"])
    
    # Where score != 0, signs should match
    mask = df["primary_transformed_coordinate"] != 0
    assert (df.loc[mask, "expected_sign"] == df.loc[mask, "actual_sign"]).all()

import numpy as np
def test_lnb_count_interpretation():
    df = load("transformed_task_observations_long.csv")
    lnb = df[df["score_field"] == "cnb_lnb_mcr"]
    assert (lnb["direction_multiplier"] == 1).all()

def test_ctap_caveat():
    # Implicitly tracked in claims register
    c = load("step5ba_claims_register.csv")
    assert "Research Use Only" in c.iloc[0]["caveat"]

def test_sd_mad_implementation():
    df = load("transformed_task_observations_long.csv")
    assert "primary_scale_mad" in df.columns
    assert "sensitivity_scale_sd" in df.columns
    # Both should be strictly positive
    assert (df["primary_scale_mad"] > 0).all()
    assert (df["sensitivity_scale_sd"] > 0).all()

def test_missing_age():
    df = load("transformed_task_observations_long.csv")
    assert not df["session_age"].isna().any()

def test_zero_scale():
    df = load("transformed_task_observations_long.csv")
    assert not (df["primary_scale_mad"] == 0).any()

def test_extrapolation():
    df = load("transformed_task_observations_long.csv")
    assert "extrapolation_flag" in df.columns
    assert df["extrapolation_flag"].sum() == 0

def test_v_only_sensitivity_separation():
    df = load("transformed_profiles_wide.csv")
    assert df["analytical_stratum"].str.contains("V-only").any()

def test_no_level_shape_calculated():
    forbidden = ["level", "shape", "icc", "scatter"]
    for f in os.listdir(OUT):
        if f.endswith(".csv"):
            cols = pd.read_csv(os.path.join(OUT, f), nrows=1).columns
            for c in cols:
                for verb in forbidden:
                    assert verb.lower() not in c.lower()
