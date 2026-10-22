import pandas as pd
import json
import numpy as np

out_dir = r'C:\Users\asmi\Desktop\Projects\CHAVI\chavi_analysis_ds007116_step5ba_transformed_data_20260916'

long_df = pd.read_csv(f'{out_dir}\\transformed_task_observations_long.csv')

print(f'Total rows in long format: {len(long_df)}')
occasions = long_df[['participant_id', 'repository_session_id', 'cohort_type']].drop_duplicates()
print(f'Total unique occasions (participant + session): {len(long_df[["participant_id", "repository_session_id"]].drop_duplicates())}')

primary = long_df[long_df['cohort_type'].str.contains('Primary')]
v_only = long_df[long_df['cohort_type'].str.contains('V-only')]
print(f'Primary V/F: {primary["participant_id"].nunique()} pts, {len(primary[["participant_id", "repository_session_id"]].drop_duplicates())} occasions, {len(primary)} rows')
print(f'V-only: {v_only["participant_id"].nunique()} pts, {len(v_only[["participant_id", "repository_session_id"]].drop_duplicates())} occasions, {len(v_only)} rows')

primary_keys = set(zip(primary['participant_id'], primary['repository_session_id']))
v_only_keys = set(zip(v_only['participant_id'], v_only['repository_session_id']))
print(f'Is V-only occasions a subset of Primary occasions? {v_only_keys.issubset(primary_keys)}')

both = primary_keys.intersection(v_only_keys)
print(f'Source occasions in BOTH strata: {len(both)}')
print(f'Task rows in BOTH strata: {len(both) * 5}')

cross = pd.read_csv(f'{out_dir}\\transformation_manual_crosscheck.csv').iloc[0]
task = cross['task']
fold = cross['fold']
match = long_df[(long_df['score_field'] == task) & (long_df['fold'] == fold) & (np.isclose(long_df['raw_value'], cross['raw']))].iloc[0]

param_err = abs(match['predicted_reference_value'] - cross['mean']) + abs(match['primary_scale_mad'] - cross['mad'])
coord_err = abs(match['primary_transformed_coordinate'] - cross['expected_coord'])
print(f'Max param error: {param_err}')
print(f'Max coord error: {coord_err}')

print(f'Extrapolation flags count: {long_df["extrapolation_flag"].sum()}')
