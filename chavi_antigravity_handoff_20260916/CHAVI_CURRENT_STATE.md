# CHAVI Current State

## Summary
The current stage of the CHAVI project is at the completion of **Step 5A**. Step 5B has not been started. The next expected action is a supervisor decision-freeze and transformation-feasibility step.

## Dataset Status
- Dataset: OpenNeuro `ds007116`
- Commit: `fc7dc36fa2598b0b2e4579baef37d148cc085207`
- Tag: `1.0.6`
- 132 registered participants, 225 recorded session rows, 41 verified phenotype payloads.

## Cohort Status
- 52 participants form the synchronized profile-first candidate primary cohort (two jointly complete synchronized occasions).
- 109 participants have at least one complete occasion.
- 176 complete synchronized occasions available.
- Count reconciliation is exact: 53 participants present in intersection of five task-pair cohorts; 50 where task pairs used the same earlier and later labels; 52 from raw same-session complete V/F occasions (which adds sub-20259 and sub-20494, and excludes sub-21035).

## Verified Task-Level Dependability (Step 4B)
- Letter N-back (55 pairs): ICC(A,1) = 0.660377 [0.279, 0.855], Mean change = 0.000 [-0.636, 0.618]
- Face Memory (59 pairs): ICC(A,1) = 0.560473 [0.344, 0.719], Mean change = 0.847 [-0.373, 2.034]
- Matrix Reasoning (57 pairs): ICC(A,1) = 0.747309 [0.565, 0.850], Mean change = 0.228 [-0.526, 1.018]
- Emotion Recognition (58 pairs): ICC(A,1) = 0.272176 [0.123, 0.528], Mean change = 1.845 [0.897, 2.966]
- Dominant Finger Tapping (57 pairs): ICC(A,1) = 0.463781 [0.316, 0.584], Mean change = 4.795 [2.842, 6.836]

## Methodological Boundaries
- Exact V/F QC for candidate primary cohort.
- No primary imputation.
- Participant is the resampling unit.
- CTAP caveat included.
- Step 5A produced draft specifications for transformation contract (elevation, shape, etc.) but no values have been generated.
