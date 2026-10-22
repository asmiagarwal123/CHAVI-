import pandas as pd
import numpy as np
import os
import json
import yaml
import pytest

ROOT = r"C:\Users\asmi\Desktop\Projects\CHAVI"
OUT = os.path.join(ROOT, "chavi_analysis_ds007116_step5bar3_final_validation_20260916")

def test_contract_and_provenance():
    with open(os.path.join(ROOT, "chavi_analysis_ds007116_step5af_contract_freeze_20260916", "step5af_transformation_contract_frozen.json")) as f:
        contract = json.load(f)
    assert contract["age_model_primary"] == "M0_no_age_adjustment"
    assert "M1" in contract.get("age_model_spline_excluded", "")
    assert "M2" in contract.get("age_model_spline_excluded", "")
    assert "MAD_primary_SD_sensitivity" in contract["scale_estimator_primary"]

def test_counts_and_strata():
    df_primary = pd.read_csv(os.path.join(OUT, "primary_vf_transformed_rows.csv"))
    assert df_primary["participant_id"].nunique() == 52
    assert len(df_primary[["participant_id", "repository_session_id"]].drop_duplicates()) == 104
    assert len(df_primary) == 520

    df_vonly = pd.read_csv(os.path.join(OUT, "vonly_transformed_rows.csv"))
    assert df_vonly["participant_id"].nunique() == 45
    assert len(df_vonly[["participant_id", "repository_session_id"]].drop_duplicates()) == 90
    assert len(df_vonly) == 450

    df_stratified = pd.read_csv(os.path.join(OUT, "stratified_transformed_rows.csv"))
    assert len(df_stratified) == 970
    assert not df_stratified["analytical_stratum"].str.contains(",").any()

def test_parameters_and_transformations():
    # Verify values from the validator crosscheck
    crosscheck = pd.read_csv(os.path.join(OUT, "parameter_crosscheck_all_folds.csv"))
    assert crosscheck["max_abs_err_mean"].max() < 1e-6
    assert crosscheck["max_abs_err_scale"].max() < 1e-6
    
    coord_crosscheck = pd.read_csv(os.path.join(OUT, "coordinate_crosscheck_expanded.csv"))
    assert coord_crosscheck["err_m0_mad"].max() < 1e-6
    assert coord_crosscheck["err_m0_sd"].max() < 1e-6

def test_support_behavior():
    df_strat = pd.read_csv(os.path.join(OUT, "stratified_transformed_rows.csv"))
    assert df_strat["primary_m0_mad_coordinate"].notna().all()
    assert df_strat["m0_sd_sensitivity_coordinate"].notna().all()
    
    # M1 only missing when unsupported
    m1_missing = df_strat[df_strat["m1_age_sensitivity_coordinate"].isna()]
    assert (m1_missing["m1_supported"] == False).all()
    
    m1_extrap = pd.read_csv(os.path.join(OUT, "m1_extrapolation_and_support_audit.csv"))
    assert "m1_extrapolation_flag" in m1_extrap.columns

def test_scope():
    df_strat = pd.read_csv(os.path.join(OUT, "stratified_transformed_rows.csv"))
    forbidden = ["level", "shape", "scatter", "icc", "simulation"]
    for col in df_strat.columns:
        for f in forbidden:
            assert f not in col.lower()
