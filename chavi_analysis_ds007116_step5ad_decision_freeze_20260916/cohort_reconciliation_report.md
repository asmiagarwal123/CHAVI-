# Cohort Reconciliation Report

## Objective
To independently reconstruct and verify the CHAVI Step 5A candidate primary profile cohort from the original Step 3B `task_observations_long.csv`.

## Process
1. Filtered raw observations for the five selected tasks: `cnb_lnb_mcr`, `cnb_cpf_cr`, `cnb_pmat_cr`, `cnb_er40_cr`, `cnb_ctap_dom`.
2. Applied strict QC rule by filtering for `eligible_documented_valid_or_likely_valid == 'yes'`.
3. Grouped by `participant_id` and `repository_session_id`.
4. Kept only occasions where all 5 task scores were present.
5. Calculated counts based on these complete, synchronized occasions.

## Results
- Registered participants: 132
- Participants with valid data in selected tasks: 119
- Complete synchronized V/F occasions: **176** (Matches Step 5A exactly)
- Participants with at least one complete synchronized occasion: **109** (Matches Step 5A exactly)
- Participants with two jointly complete synchronized occasions: **52** (Matches Step 5A exactly)

## Discrepancy Trace
No discrepancy found. The 176 / 109 / 52 counts perfectly matched the target cohort size specified in the Step 5A records. The 50/52/53 reconciliation is fully supported by the empirical data.

## Verdict
**REPRODUCTION SUCCESSFUL**. The candidate primary denominator of 52 participants is verified and can be used for transformation diagnostics.
