import pandas as pd
import numpy as np
import os
import json
import hashlib
import subprocess
import datetime
from sklearn.model_selection import GroupKFold
import statsmodels.api as sm
import statsmodels.formula.api as smf

def get_git_info(repo_dir):
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir).decode('utf-8').strip()
        tag = subprocess.check_output(['git', 'describe', '--tags'], cwd=repo_dir).decode('utf-8').strip()
        status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo_dir).decode('utf-8').strip()
        return commit, tag, status
    except Exception as e:
        return str(e), "", ""

def hash_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def reproduce_cohort(df):
    print("Reproducing cohort...")
    # 132 registered - assumed present in full demographic
    # We look at task_observations_long
    df_valid = df[df['eligible_documented_valid_or_likely_valid'] == 'yes'].copy()
    
    # Selected tasks
    selected_tasks = ['cnb_lnb_mcr', 'cnb_cpf_cr', 'cnb_pmat_cr', 'cnb_er40_cr', 'cnb_ctap_dom']
    
    # Filter for selected tasks
    df_tasks = df_valid[df_valid['score_field'].isin(selected_tasks)].copy()
    
    unique_participants = df_tasks['participant_id'].nunique()
    print(f"Participants with valid data in selected tasks: {unique_participants}")
    
    # Synchronize occasions: require all 5 tasks for a (participant_id, repository_session_id)
    occasion_counts = df_tasks.groupby(['participant_id', 'repository_session_id'])['score_field'].nunique().reset_index()
    complete_occasions = occasion_counts[occasion_counts['score_field'] == 5]
    
    num_complete_occasions = len(complete_occasions)
    print(f"Complete synchronized V/F occasions: {num_complete_occasions}")
    
    participants_with_1plus = complete_occasions['participant_id'].nunique()
    print(f"Participants with >= 1 complete occasion: {participants_with_1plus}")
    
    participant_occasion_counts = complete_occasions.groupby('participant_id').size()
    participants_with_2plus = participant_occasion_counts[participant_occasion_counts >= 2].index.tolist()
    print(f"Participants with >= 2 jointly complete occasions: {len(participants_with_2plus)}")
    
    # Construct candidate primary cohort: The first two jointly complete occasions for the 52 participants
    # First, get all complete occasion data
    complete_keys = complete_occasions[['participant_id', 'repository_session_id']]
    df_complete = pd.merge(df_tasks, complete_keys, on=['participant_id', 'repository_session_id'], how='inner')
    
    # Sort by session
    df_complete = df_complete.sort_values(['participant_id', 'repository_session_id', 'score_field'])
    
    candidate_cohort = df_complete[df_complete['participant_id'].isin(participants_with_2plus)]
    
    return {
        'total_valid_participants': unique_participants,
        'complete_occasions': num_complete_occasions,
        'participants_with_1plus': participants_with_1plus,
        'participants_with_2plus': len(participants_with_2plus),
        'candidate_participants': participants_with_2plus,
        'candidate_df': candidate_cohort,
        'complete_occasions_df': df_complete
    }

def grouped_cross_fitting(df, k=5, seed=42):
    print("Performing Grouped Cross-Fitting...")
    gkf = GroupKFold(n_splits=k)
    # Using participant_id as group
    # We want to do this at the occasion level or observation level?
    # Better to do it at participant level to avoid leakage
    participants = df['participant_id'].unique()
    # Dummy X, y
    X = np.zeros(len(participants))
    
    folds = []
    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(X, groups=participants)):
        train_parts = participants[train_idx]
        test_parts = participants[test_idx]
        
        for p in test_parts:
            folds.append({'participant_id': p, 'fold': fold_idx})
            
    return pd.DataFrame(folds)

def age_model_feasibility(df, folds_df):
    print("Evaluating Age Models...")
    # Merge folds
    df_eval = pd.merge(df, folds_df, on='participant_id', how='left')
    
    tasks = ['cnb_lnb_mcr', 'cnb_cpf_cr', 'cnb_pmat_cr', 'cnb_er40_cr', 'cnb_ctap_dom']
    
    results = []
    for task in tasks:
        df_task = df_eval[df_eval['score_field'] == task].copy()
        df_task = df_task.dropna(subset=['original_value', 'session_age'])
        
        for fold in range(5):
            train = df_task[df_task['fold'] != fold]
            test = df_task[df_task['fold'] == fold]
            
            if len(train) == 0 or len(test) == 0:
                continue
                
            # Model 0: Intercept
            m0 = smf.ols('original_value ~ 1', data=train).fit()
            pred0 = m0.predict(test)
            rmse0 = np.sqrt(np.mean((test['original_value'] - pred0)**2))
            
            # Model 1: Linear
            m1 = smf.ols('original_value ~ session_age', data=train).fit()
            pred1 = m1.predict(test)
            rmse1 = np.sqrt(np.mean((test['original_value'] - pred1)**2))
            
            # Model 2: Natural Spline (df=3)
            try:
                m2 = smf.ols('original_value ~ cr(session_age, df=3)', data=train).fit()
                pred2 = m2.predict(test)
                rmse2 = np.sqrt(np.mean((test['original_value'] - pred2)**2))
            except:
                rmse2 = np.nan
                
            results.append({
                'task': task,
                'fold': fold,
                'rmse0': rmse0,
                'rmse1': rmse1,
                'rmse2': rmse2
            })
            
    return pd.DataFrame(results)

def main():
    root_dir = r"C:\Users\asmi\Desktop\Projects\CHAVI"
    dataset_dir = os.path.join(root_dir, "ds007116")
    output_dir = os.path.join(root_dir, "chavi_analysis_ds007116_step5ad_decision_freeze_20260916")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Checking dataset...")
    commit, tag, status = get_git_info(dataset_dir)
    print(f"Commit: {commit}, Tag: {tag}, Status: {status}")
    
    input_file = os.path.join(root_dir, "chavi_audit_ds007116_step3b_20260909", "task_observations_long.csv")
    input_hash = hash_file(input_file)
    print(f"Input Hash: {input_hash}")
    
    df = pd.read_csv(input_file)
    
    cohort_stats = reproduce_cohort(df)
    
    pd.DataFrame({'participant_id': cohort_stats['candidate_participants']}).to_csv(os.path.join(output_dir, 'cohort_reproduction.csv'), index=False)
    
    # Cross fitting
    folds_df = grouped_cross_fitting(cohort_stats['complete_occasions_df'])
    folds_df.to_csv(os.path.join(output_dir, 'participant_grouped_fold_manifest.csv'), index=False)
    
    # Age models
    age_results = age_model_feasibility(cohort_stats['complete_occasions_df'], folds_df)
    age_results.to_csv(os.path.join(output_dir, 'age_model_comparison.csv'), index=False)
    
    # Write provenance
    prov = {
        "dataset_commit": commit,
        "dataset_tag": tag,
        "input_hash": input_hash,
        "cohort_counts": {
            "complete_occasions": cohort_stats['complete_occasions'],
            "participants_1plus": cohort_stats['participants_with_1plus'],
            "participants_2plus": cohort_stats['participants_with_2plus']
        },
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    with open(os.path.join(output_dir, 'step5ad_provenance.json'), 'w') as f:
        json.dump(prov, f, indent=2)
        
    # Draft contract
    contract = {
        "contract_version": "0.1.0",
        "input_dataset_identity": "OpenNeuro ds007116",
        "input_hashes": {"task_observations_long.csv": input_hash},
        "task_fields": ['cnb_lnb_mcr', 'cnb_cpf_cr', 'cnb_pmat_cr', 'cnb_er40_cr', 'cnb_ctap_dom'],
        "task_directions": {"default": "positive"},
        "eligible_qc_states": ["V"],
        "primary_cohort_definition": "52 participants with two jointly complete synchronized V/F occasions",
        "synchronization_rule": "Same session, all 5 tasks present",
        "reference_cohort_definition": "Baseline-reference cohort (Option A)",
        "participant_grouping_rule": "Deterministic participant-grouped",
        "fold_seed": 42,
        "fold_count": 5,
        "age_model": "PENDING",
        "model_hyperparameters": {},
        "model_selection_rule": "Conservative, linear unless strong nonlinear evidence",
        "scale_estimator": "SD or robust MAD",
        "zero_scale_handling": "Refuse",
        "extrapolation_policy": "Flag and restrict",
        "missingness_policy": "No primary imputation",
        "extreme_value_policy": "Retain, use influence diagnostics",
        "transformation_uncertainty_plan": "Refit-within-bootstrap",
        "primary_coordinate": "Age-referenced Z-score",
        "sensitivity_coordinates": ["Raw Z-score without age adjustment"],
        "profile_estimand_hierarchy": ["Level", "Centered Shape", "Scatter", "Shape-change RMSE"],
        "forbidden_claims": ["Clinical validity", "Diagnostic value", "Population norms"],
        "status": "not_ready",
        "unresolved_blockers": ["pending_human_approval"]
    }
    
    with open(os.path.join(output_dir, 'step5ad_transformation_contract_draft.json'), 'w') as f:
        json.dump(contract, f, indent=2)
        
    print("Execution complete.")

if __name__ == "__main__":
    main()
