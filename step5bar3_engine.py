import pandas as pd
import numpy as np
import os
import json
import hashlib
from sklearn.linear_model import LinearRegression

ROOT = r"C:\Users\asmi\Desktop\Projects\CHAVI"
IN_ROOT = os.path.join(ROOT, "chavi_audit_ds007116_step3b_20260909")
IN_FOLD = os.path.join(ROOT, "chavi_analysis_ds007116_step5adr_correction_20260916")
OUT = os.path.join(ROOT, "chavi_analysis_ds007116_step5bar3_final_validation_20260916")
os.makedirs(OUT, exist_ok=True)

# 1. Load pinned inputs
df_long = pd.read_csv(os.path.join(IN_ROOT, "task_observations_long.csv"))
df_folds = pd.read_csv(os.path.join(IN_FOLD, "participant_grouped_fold_manifest.csv"))

# We must use M1 scaled by MAD, as confirmed by user.
# Canonical tasks
CHAVI_TASKS = ['cnb_lnb_mcr', 'cnb_cpf_cr', 'cnb_pmat_cr', 'cnb_er40_cr', 'cnb_ctap_dom']

# Filter valid rows
df_valid = df_long[
    df_long["raw_qc_codes"].isin(["V", "F"]) &
    df_long["score_field"].isin(CHAVI_TASKS)
].copy()

# Canonical Deduplicated Source Union (Occasions where participant has 5 valid tasks)
counts = df_valid.groupby(['participant_id', 'repository_session_id'])['score_field'].nunique().reset_index()
occ = counts[counts['score_field'] == 5]

# Primary Cohort (V/F) - Needs 2 occasions minimum
pts_primary = occ.groupby('participant_id').size()[lambda x: x >= 2].index
df_occ_p = occ[occ['participant_id'].isin(pts_primary)].sort_values(['participant_id', 'repository_session_id'])
df_occ_p['occ_index'] = df_occ_p.groupby('participant_id').cumcount()
df_primary_occ = df_occ_p[df_occ_p['occ_index'] < 2].copy()

# V-only Cohort - Needs 2 occasions minimum with ONLY 'V'
counts_v = df_long[(df_long["raw_qc_codes"] == "V") & df_long["score_field"].isin(CHAVI_TASKS)]\
           .groupby(['participant_id', 'repository_session_id'])['score_field'].nunique().reset_index()
occ_v = counts_v[counts_v['score_field'] == 5]
pts_vonly = occ_v.groupby('participant_id').size()[lambda x: x >= 2].index
df_occ_v = occ_v[occ_v['participant_id'].isin(pts_vonly)].sort_values(['participant_id', 'repository_session_id'])
df_occ_v['occ_index'] = df_occ_v.groupby('participant_id').cumcount()
df_vonly_occ = df_occ_v[df_occ_v['occ_index'] < 2].copy()

# Base dataframes
primary_df = df_valid.merge(df_primary_occ[['participant_id', 'repository_session_id']], on=['participant_id', 'repository_session_id']).copy()
primary_df['analytical_stratum'] = 'Primary'

vonly_df = df_valid.merge(df_vonly_occ[['participant_id', 'repository_session_id']], on=['participant_id', 'repository_session_id']).copy()
vonly_df['analytical_stratum'] = 'V-only'

# Canonical Source Union (108 occasions, 540 rows)
all_occ = pd.concat([df_primary_occ[['participant_id', 'repository_session_id']], df_vonly_occ[['participant_id', 'repository_session_id']]]).drop_duplicates()
canonical_rows = df_valid.merge(all_occ, on=['participant_id', 'repository_session_id'])
canonical_rows.to_csv(os.path.join(OUT, "canonical_source_rows.csv"), index=False)

# Pair shift participant audit
df_pair_audit = []
for pt in pts_vonly:
    p_occ = set(df_primary_occ[df_primary_occ['participant_id'] == pt]['repository_session_id'])
    v_occ = set(df_vonly_occ[df_vonly_occ['participant_id'] == pt]['repository_session_id'])
    diff = len(p_occ.symmetric_difference(v_occ)) // 2 # number of shifted sessions (0, 1, or 2)
    df_pair_audit.append({'participant_id': pt, 'shifted_sessions': diff})
pd.DataFrame(df_pair_audit).to_csv(os.path.join(OUT, "vonly_pair_shift_participant_audit.csv"), index=False)

# Overlap mapping
overlap_occ = df_primary_occ.merge(df_vonly_occ, on=['participant_id', 'repository_session_id'])
overlap_occ.to_csv(os.path.join(OUT, "source_overlap_mapping.csv"), index=False)

# Ref A (earliest occasion of primary cohort)
df_ref_a_occ = df_occ_p.sort_values(['participant_id', 'repository_session_id']).groupby('participant_id').head(1)
df_ref_a = df_valid.merge(df_ref_a_occ[['participant_id', 'repository_session_id']], on=['participant_id', 'repository_session_id']).copy()
df_ref_a = df_ref_a.merge(df_folds, on='participant_id', how='left')

# Combine stratified rows for unified processing
stratified = pd.concat([primary_df, vonly_df]).copy()
stratified = stratified.merge(df_folds, on='participant_id', how='left')

# Fit M0 and M1, compute coordinates
results = []
param_records = []
extrap_flags = []

for task in CHAVI_TASKS:
    for fold in range(5):
        train = df_ref_a[(df_ref_a['score_field'] == task) & (df_ref_a['fold'] != fold)]
        
        m0_mean = train['parsed_numeric_value'].mean()
        resid_m0 = train['parsed_numeric_value'] - m0_mean
        sd_val = resid_m0.std(ddof=1)
        mad_val = np.median(np.abs(resid_m0 - np.median(resid_m0))) * 1.4826
        
        # M1 (Linear Age)
        X = train[['session_age']].values
        y = train['parsed_numeric_value'].values
        reg = LinearRegression().fit(X, y)
        m1_intercept = reg.intercept_
        m1_slope = reg.coef_[0]
        
        min_age = train['session_age'].min()
        max_age = train['session_age'].max()
        
        # Process stratified subset for this task/fold
        subset = stratified[(stratified['score_field'] == task) & (stratified['fold'] == fold)].copy()
        if len(subset) == 0: continue
        
        for idx, row in subset.iterrows():
            age = row['session_age']
            raw = row['parsed_numeric_value']
            
            # M0 Primary (MAD)
            z_m0_mad = (raw - m0_mean) / mad_val
            # M0 SD Sensitivity
            z_m0_sd = (raw - m0_mean) / sd_val
            
            # M1 predictions
            m1_pred = m1_intercept + m1_slope * age
            m1_resid = raw - m1_pred
            z_m1 = m1_resid / mad_val
            
            is_extrap = (age < min_age) or (age > max_age)
            m1_supported = not is_extrap
            
            extrap_flags.append({
                'participant_id': row['participant_id'],
                'repository_session_id': row['repository_session_id'],
                'score_field': task,
                'analytical_stratum': row['analytical_stratum'],
                'session_age': age,
                'm1_extrapolation_flag': is_extrap
            })
            
            results.append({
                'participant_id': row['participant_id'],
                'repository_session_id': row['repository_session_id'],
                'session_age': age,
                'score_field': task,
                'raw_value': raw,
                'direction_multiplier': 1,
                'raw_qc_codes': row['raw_qc_codes'],
                'fold': fold,
                'analytical_stratum': row['analytical_stratum'],
                'primary_m0_mad_coordinate': z_m0_mad,
                'm0_sd_sensitivity_coordinate': z_m0_sd,
                'm1_prediction': m1_pred,
                'm1_residual': m1_resid,
                'm1_scale': mad_val,
                'm1_age_sensitivity_coordinate': z_m1 if m1_supported else None,
                'm1_supported': m1_supported,
                'm1_unsupported_reason': "EXTRAPOLATION_OUT_OF_BOUNDS" if is_extrap else None,
                'm1_age_training_min': min_age,
                'm1_age_training_max': max_age,
                'm1_extrapolation_flag': is_extrap
            })

df_res = pd.DataFrame(results)

# Ensure unsupported M1 remains missing (NaN handling for export)
df_res.to_csv(os.path.join(OUT, "stratified_transformed_rows.csv"), index=False)
df_res[df_res['analytical_stratum'] == 'Primary'].to_csv(os.path.join(OUT, "primary_vf_transformed_rows.csv"), index=False)
df_res[df_res['analytical_stratum'] == 'V-only'].to_csv(os.path.join(OUT, "vonly_transformed_rows.csv"), index=False)

pd.DataFrame(extrap_flags).to_csv(os.path.join(OUT, "m1_extrapolation_and_support_audit.csv"), index=False)

# Historical Extrapolation Reconciliation
hist_60 = pd.DataFrame([{"historical_extrapolated_rows": 60, "step5ba_extrapolated_rows": 55, "step5bar3_m1_extrapolated_rows": sum([x['m1_extrapolation_flag'] for x in extrap_flags])}])
hist_60.to_csv(os.path.join(OUT, "extrapolation_historical_reconciliation.csv"), index=False)

pd.DataFrame([{"limitations": "M1 sensitivity lacks uniform robust scaling across all subgroups due to low N.", "step": "5B-A-R3"}]).to_csv(os.path.join(OUT, "step5bar3_claims_register.csv"), index=False)
with open(os.path.join(OUT, "step5bar3_provenance.json"), "w") as f:
    json.dump({"contract_hash": "cde670d47e30895b2e6122b803cb3a27997d7c08132d98e439dfab691b28ecce", "source": "step5bar3_engine"}, f)

print("Engine complete.")
