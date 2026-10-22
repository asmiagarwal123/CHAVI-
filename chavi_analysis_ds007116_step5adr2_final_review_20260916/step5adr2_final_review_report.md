# CHAVI Step 5A-D-R2: Final Transformation-Decision Evidence Review

**Verdict:** `READY FOR SUPERVISOR APPROVAL`

This report completes the independent scientific validation and requirement-compliance checks for the CHAVI transformation pipeline prior to the decision freeze. **Step 5B (profile computation) has not been started.**

## 1. What Was Independently Reproduced

- The **176/109/52 cohort** was exactly reproduced using the documented V/F quality control policy.
- The deterministic 5-fold participant-grouped split was preserved (seed=42).
- The raw Step 3B task observation file is strictly unchanged (SHA-256 hash verified).
- No follow-up or participant leakage exists in the reference cohort modeling.

## 2. What Changed From Step 5A-D-R (R1 -> R2)

1. **Dual Reference Cohort Evaluation:** R2 implemented and compared Reference A (109 participants, all baseline) and Reference B (52 participants, longitudinal only).
2. **Age-Model Refitting:** Age models (M0, M1, M2) were rigorously cross-fitted on *both* reference cohorts.
3. **SD vs MAD Diagnostics:** Fold-level empirical comparisons of ordinary SD versus robust MAD were fully computed for all 5 tasks.
4. **Extrapolation Policy Formalized:** The exact number of affected rows (60) was calculated against the Ref A boundaries, and 4 executable prediction policies were compared.
5. **Feasibility Confidence:** The refit-within-bootstrap test was properly formalized and demonstrated 100% feasibility.
6. **Decision Matrix Completed:** All 18 decisions are now backed by firm, unambiguous empirical rules rather than conditional statements.

## 3. Final Evidence and Recommendations

### Exact LNB Interpretation
- **Verified:** `cnb_lnb_mcr` is a **COUNT of true positive responses** for 1-back and 2-back trials (range 6-20). It is *not* a response-time variable (the sibling RT variable `cnb_lnb_mrtc` carries the `ms` unit).
- **Direction:** POSITIVE (higher is better).
- **Unresolved Caveat:** The exact denominator mapping for "1-back and 2-back" within the 45-trial battery remains undocumented in the local JSON. We **cannot claim normalized accuracy**, only a count of true positives.

### Chosen Reference Cohort
- **Recommendation:** **Reference A (N=109)**.
- **Why:** Reference B (N=52) strictly conditions on participants having a second complete longitudinal occasion. This introduces *selection conditioning bias* into the internal standard. Reference A avoids this by using the earliest eligible occasion of all 109 available participants.

### Chosen Age Policy
- **Recommendation:** **M0 (No Age Adjustment) Primary**.
- **Why:** Using a prespecified rule (linear adopted only if >2% OOF RMSE improvement AND mean slope p < 0.10), **0/5 tasks** met all criteria for linear adjustment. The data (N~109 baseline) do not support the instability of linear adjustment. M1 remains as a sensitivity coordinate. M2 (spline) is formally excluded due to overfitting risks on small folds.

### Chosen Scale
- **Recommendation:** **MAD Primary, SD Sensitivity**.
- **Why:** 3 out of 5 tasks (including LNB and ER40) demonstrated heavy-tailed residuals and SD/MAD ratios > 1.3, which would cause SD-scaled scores to be artificially compressed by extreme values. There were no near-zero MAD events that would break the estimator.

### Exact Extrapolation Algorithm
- **Recommendation:** **P3 (Use No-Age Coordinate)**.
- **Why:** 60 task rows (from 12 unique participants) fall outside the training age boundaries at follow-up. Rather than capping age (bias) or refusing the participant (data loss), P3 marks the age-adjusted coordinate as `UNSUPPORTED` and uses the robust M0 (no age) coordinate instead.

### Bootstrap Feasibility
- **Verdict:** **Feasible (100.0% valid replicates)**.
- **Why:** Reconstructing the reference cohort and refitting models/scales within each bootstrap replicate works reliably. The contract is set to target 5,000 valid replicates, falling back to a fixed transformation only if <95% succeed.

## 4. Remaining Caveats

1. **LNB Denominator:** Unresolved (see above).
2. **CTAP Units:** Direction is positive (taps), but specific aggregation semantics remain unverified.
3. **Task-Version Equivalence:** We assume the digital implementations of tasks were equivalent across the 2-year interval.
4. **Conditional SEM:** Standard error of measurement estimates inherently assume a static true score. In adolescents over a 2-year interval, "true" developmental change confounds reliability estimates.

## 5. Artifacts and Verification

- **Tests Passed:** 74/74 (covering all 25+ specific user prompt requirements).
- **Files Created:** 16 (including the final draft `step5adr2_transformation_contract_candidate.json`, full decision matrix, and all supporting diagnostic CSVs).
- **Dataset Integrity:** Clean git status, unchanged Step 3B file hashes.

---
**Status:** I have completed the final evidence review and generated the non-destructive R2 workspace. I am stopping here. **I have not begun Step 5B.** Awaiting your final review of the 18 decisions.
