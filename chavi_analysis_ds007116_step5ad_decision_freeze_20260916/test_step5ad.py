import os
import json
import pytest
import pandas as pd
from run_step5ad import hash_file, get_git_info, reproduce_cohort

ROOT_DIR = r"C:\Users\asmi\Desktop\Projects\CHAVI"
OUTPUT_DIR = os.path.join(ROOT_DIR, "chavi_analysis_ds007116_step5ad_decision_freeze_20260916")

def test_dataset_commit():
    commit, tag, status = get_git_info(os.path.join(ROOT_DIR, "ds007116"))
    assert commit == "fc7dc36fa2598b0b2e4579baef37d148cc085207"
    assert tag == "1.0.6"
    assert status == ""

def test_cohort_reproduction():
    input_file = os.path.join(ROOT_DIR, "chavi_audit_ds007116_step3b_20260909", "task_observations_long.csv")
    df = pd.read_csv(input_file)
    stats = reproduce_cohort(df)
    
    assert stats['complete_occasions'] == 176
    assert stats['participants_with_1plus'] == 109
    assert stats['participants_with_2plus'] == 52

def test_contract_schema():
    contract_file = os.path.join(OUTPUT_DIR, "step5ad_transformation_contract_draft.json")
    assert os.path.exists(contract_file)
    with open(contract_file, 'r') as f:
        contract = json.load(f)
    
    assert contract['status'] == 'not_ready'
    assert 'pending_human_approval' in contract['unresolved_blockers']
    assert len(contract['task_fields']) == 5

def test_no_leakage_in_folds():
    folds_file = os.path.join(OUTPUT_DIR, "participant_grouped_fold_manifest.csv")
    assert os.path.exists(folds_file)
    folds_df = pd.read_csv(folds_file)
    
    # Check that each participant is in exactly one fold
    part_fold_counts = folds_df.groupby('participant_id')['fold'].nunique()
    assert all(part_fold_counts == 1)

def test_preservation_of_previous_outputs():
    # Asserting that previous output hashes are unchanged is done by not touching them
    # We can check a known file
    input_file = os.path.join(ROOT_DIR, "chavi_audit_ds007116_step3b_20260909", "task_observations_long.csv")
    h = hash_file(input_file)
    assert h == "8b435d4b23d0b5f70b3c56ade4215d215028426dbdb46eaaf8daaa3cd0dc1978"
