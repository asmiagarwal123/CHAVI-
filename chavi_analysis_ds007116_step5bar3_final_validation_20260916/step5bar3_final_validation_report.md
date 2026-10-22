# Step 5B-A-R3 Final Validation Report

## Contract Interpretation and M1 Resolution
An independent review of the frozen contract versus the supervisor approval (`SUPERVISOR_APPROVAL.yaml`) revealed that the M1 linear-age sensitivity analysis was approved, but the JSON contract inadvertently omitted it from the `sensitivity_coordinates` array. Furthermore, the explicit scale denominator to use for M1 residuals was undefined.

Following explicit instruction and user feedback, we resolved this conflict:
- **M1 Sensitivity Restoration**: The M1 linear-age sensitivity model has been fully incorporated into the pipeline as an independent coordinate type.
- **M1 Scale Resolution**: M1 residuals are scaled by **MAD**, applying the primary scale estimator identically to the sensitivity model to preserve heavy-tail robustness uniformly.

## Counts and Stratified Representation
We eliminated ambiguous deduplication techniques in favor of strict `analytical_stratum` identifiers:
- **Canonical Occasions**: 108 unique canonical occasions comprising exactly 540 task rows.
- **Primary Stratum**: 52 participants, 104 occasions, 520 task rows.
- **V-only Stratum**: 45 participants, 90 occasions, 450 task rows.
- **Stratified Total**: By unioning the independent sets without mathematically combining overlapping properties, exactly 970 stratified task rows were exported.

## Shifted Pair Analysis
The V-only sensitivity stratum enforces a stricter QC bound. The exact participant overlap mapping revealed:
- 86 occasions (430 rows) perfectly overlap between the Primary and V-only strata.
- Some participants shifted their chronological occasion anchors (e.g., from ses-1 to ses-2) because of the stringent "V" quality filter, which structurally altered their baseline comparisons in the independent V-only models.

## Parameter and Coordinate Validation
An independent Pytest suite (`test_step5bar3_independent.py`) and an independent script (`independent_transformation_validator.py`) recomputed 100% of the metrics completely from mathematical first-principles:
- **Parameter Validation**: 25 crosschecks completely verified mean, MAD, SD, intercept, and slope. Max parameter error = 0.0.
- **Coordinate Validation**: Expanded checks confirmed M0, M1, predictions, residuals, and support flags match script outputs natively. Max coordinate discrepancy = 0.0.

## M1 Extrapolation Reconciliation
- **Historical (60)**: Step 5A-D overcounted due to measuring a non-uniform 3rd occasion for overlapping subsets.
- **Step 5B-A (55)**: Correctly isolated chronologically anchored occasions but improperly applied the age-extrapolated boolean to the M0 age-independent model.
- **Current R3 Resolution**: The M1 linear-age model properly absorbs the extrapolation boundaries based solely on fold-specific Ref A max/min boundaries. Unsupported coordinates are explicitly cast as missing. M0 never assumes an extrapolated identity.
