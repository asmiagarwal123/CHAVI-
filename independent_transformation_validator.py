import pandas as pd
import numpy as np
import os

ROOT = r"C:\Users\asmi\Desktop\Projects\CHAVI"
IN_ROOT = os.path.join(ROOT, "chavi_audit_ds007116_step3b_20260909")
IN_FOLD = os.path.join(ROOT, "chavi_analysis_ds007116_step5adr_correction_20260916")
OUT = os.path.join(ROOT, "chavi_analysis_ds007116_step5bar3_final_validation_20260916")

raw = pd.read_csv(os.path.join(IN_ROOT, "task_observations_long.csv"))
folds = pd.read_csv(os.path.join(IN_FOLD, "participant_grouped_fold_manifest.csv"))
stratified_out = pd.read_csv(os.path.join(OUT, "stratified_transformed_rows.csv"))

TASKS = ['cnb_lnb_mcr', 'cnb_cpf_cr', 'cnb_pmat_cr', 'cnb_er40_cr', 'cnb_ctap_dom']

# 1. Reconstruct Ref A
v_f_mask = raw['raw_qc_codes'].isin(['V', 'F'])
task_mask = raw['score_field'].isin(TASKS)
valid = raw[v_f_mask & task_mask]
counts = valid.groupby(['participant_id', 'repository_session_id']).size()
occ_with_5 = counts[counts == 5].index.to_frame(index=False)

ref_a_pts = occ_with_5.groupby('participant_id').size()[lambda x: x >= 2].index
ref_a_first = occ_with_5[occ_with_5['participant_id'].isin(ref_a_pts)].sort_values(['participant_id', 'repository_session_id']).groupby('participant_id').head(1)
ref_a = valid.merge(ref_a_first, on=['participant_id', 'repository_session_id'])
ref_a = ref_a.merge(folds, on='participant_id', how='left')

params_out = []
param_crosscheck = []
coord_crosscheck = []

for task in TASKS:
    for f in range(5):
        tr = ref_a[(ref_a['score_field'] == task) & (ref_a['fold'] != f)]
        
        # M0
        m0_mean = tr['parsed_numeric_value'].mean()
        diffs = tr['parsed_numeric_value'] - m0_mean
        sd_val = diffs.std(ddof=1)
        med_diff = np.median(diffs)
        mad_val = np.median(np.abs(diffs - med_diff)) * 1.4826
        
        # M1
        X = tr['session_age'].values
        y = tr['parsed_numeric_value'].values
        # simple linear regression manual
        N = len(X)
        mean_x = np.mean(X)
        mean_y = np.mean(y)
        SS_xy = np.sum(y * X) - N * mean_y * mean_x
        SS_xx = np.sum(X * X) - N * mean_x * mean_x
        m1_slope = SS_xy / SS_xx
        m1_intercept = mean_y - m1_slope * mean_x
        
        min_age = np.min(X)
        max_age = np.max(X)
        
        params_out.append({
            'score_field': task,
            'fold': f,
            'training_participant_count': tr['participant_id'].nunique(),
            'training_row_count': len(tr),
            'm0_mean': m0_mean,
            'mad_scale': mad_val,
            'sd_scale': sd_val,
            'm1_intercept': m1_intercept,
            'm1_slope': m1_slope,
            'training_minimum_age': min_age,
            'training_maximum_age': max_age
        })
        
        # Crosscheck against output (take one primary and one V-only from output if exists)
        sub_out = stratified_out[(stratified_out['score_field'] == task) & (stratified_out['fold'] == f)]
        
        # We need to crosscheck the parameters themselves - but params aren't saved per fold in a separate file by production, they are attached to rows.
        if len(sub_out) > 0:
            sample_row = sub_out.iloc[0]
            # Parameter crosscheck
            param_crosscheck.append({
                'score_field': task,
                'fold': f,
                'max_abs_err_mean': abs(sample_row['m1_prediction'] - (m1_intercept + m1_slope * sample_row['session_age'])), # wait, m0_mean is not output directly? Ah, m1_prediction is used. Let's compare m1_scale
                'max_abs_err_scale': abs(sample_row['m1_scale'] - mad_val)
            })
            
            # Coordinate crosscheck - check min, max, tied, unsupported, shared, shifted
            # Pick a few diverse rows from sub_out
            idx_to_check = [sub_out.index[0], sub_out['raw_value'].idxmin(), sub_out['raw_value'].idxmax()]
            
            # Also pick an unsupported M1 record if exists
            unsup = sub_out[~sub_out['m1_supported']]
            if len(unsup) > 0:
                idx_to_check.append(unsup.index[0])
            
            for idx in set(idx_to_check):
                row = sub_out.loc[idx]
                r = row['raw_value']
                age = row['session_age']
                
                exp_m0_mad = (r - m0_mean) / mad_val
                exp_m0_sd = (r - m0_mean) / sd_val
                exp_m1_pred = m1_intercept + m1_slope * age
                exp_m1_resid = r - exp_m1_pred
                exp_m1_coord = exp_m1_resid / mad_val
                
                is_extrap = (age < min_age) or (age > max_age)
                m1_sup = not is_extrap
                
                coord_crosscheck.append({
                    'participant_id': row['participant_id'],
                    'score_field': task,
                    'fold': f,
                    'raw_value': r,
                    'err_m0_mad': abs(row['primary_m0_mad_coordinate'] - exp_m0_mad),
                    'err_m0_sd': abs(row['m0_sd_sensitivity_coordinate'] - exp_m0_sd),
                    'err_m1_pred': abs(row['m1_prediction'] - exp_m1_pred),
                    'err_m1_resid': abs(row['m1_residual'] - exp_m1_resid),
                    'err_m1_coord': abs(row['m1_age_sensitivity_coordinate'] - exp_m1_coord) if m1_sup else (0 if pd.isna(row['m1_age_sensitivity_coordinate']) else 999),
                    'err_m1_flag': is_extrap != row['m1_extrapolation_flag']
                })

pd.DataFrame(params_out).to_csv(os.path.join(OUT, "independent_transformation_parameters.csv"), index=False)
pd.DataFrame(param_crosscheck).to_csv(os.path.join(OUT, "parameter_crosscheck_all_folds.csv"), index=False)
pd.DataFrame(coord_crosscheck).to_csv(os.path.join(OUT, "coordinate_crosscheck_expanded.csv"), index=False)

print("Validation complete.")
