# Reproduction and Tests

## Environment
Tests were executed using `pytest test_step5ad.py`.

## Test Results
- `test_dataset_commit`: Passed. Confirmed dataset commit remains `fc7dc36fa2598b0b2e4579baef37d148cc085207` at tag `1.0.6` with a clean working tree.
- `test_cohort_reproduction`: Passed. Independently verified the 176 synchronized complete V/F occasions, 109 participants with >=1 occasion, and exactly 52 participants with >=2 occasions.
- `test_contract_schema`: Passed. Verified contract is marked `not_ready` with the explicit blocker `pending_human_approval`.
- `test_no_leakage_in_folds`: Passed. Checked that the deterministic 5-fold grouped assignment guarantees no participant is in more than one fold, meaning all occasions for a participant are grouped together.
- `test_preservation_of_previous_outputs`: Passed. Verified that historical artifacts (e.g. `task_observations_long.csv`) remain unchanged via SHA-256 hash checking.

## Conclusion
All 5 rigorous acceptance criteria tests passed successfully in 3.95s.
