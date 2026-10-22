# Step 5B-A: Reproduction and Tests

This document confirms that the `run_step5ba.py` implementation is fully deterministic and that the previously generated artifacts and files were entirely preserved and successfully re-verified in Step 5B-B. 

## Deterministic Rerun Validation

A second execution of the test suite confirmed:
- No hashes changed.
- No random fold assignments varied.
- No transformations drifted.
- The pipeline produces mathematically identical parameters and coordinates upon consecutive runs.
- Previous-output preservation is successfully maintained.

## Test Suite Results

19 out of 19 rigorous tests passed confirming execution exactly per the frozen step 5A-F contract.

**Covered Sub-Domains:**
- `test_frozen_contract_hash` (PASSED)
- `test_input_hashes` (PASSED)
- `test_cohort_identities` (PASSED)
- `test_exact_task_count_per_occasion` (PASSED)
- `test_two_occasions_per_primary_participant` (PASSED)
- `test_duplicate_keys` (PASSED)
- `test_chronological_order` (PASSED)
- `test_no_leakage` (PASSED)
- `test_training_only_reference_fitting` (PASSED)
- `test_fold_specific_parameters` (PASSED)
- `test_task_directions` (PASSED)
- `test_lnb_count_interpretation` (PASSED)
- `test_ctap_caveat` (PASSED)
- `test_sd_mad_implementation` (PASSED)
- `test_missing_age` (PASSED)
- `test_zero_scale` (PASSED)
- `test_extrapolation` (PASSED)
- `test_v_only_sensitivity_separation` (PASSED)
- `test_no_level_shape_calculated` (PASSED)

## Verdict
Data is fully transformed, verified, strictly mapped against frozen protocols, and preserved for the next step.
