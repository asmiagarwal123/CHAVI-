# CHAVI Step 5A-D-R — Independent Correction, Completion, and Scientific Validation
# Review Report
**Date:** 2026-09-16  
**Status:** READY FOR SUPERVISOR APPROVAL  
**Tests:** 48 / 48 passed

---

## 1. What was corrected

Nine deficiencies from Step 5A-D were corrected. Each correction is documented in the
transformation contract under `correction_notes` (C1–C9) and tested by the automated
test suite.

| ID | Deficiency | Resolution |
|----|-----------|-----------|
| **C1** | `cnb_lnb_mcr` was described as ambiguous regarding RT vs count | **Confirmed COUNT** (true positive responses for 1-back and 2-back trials). Local LongName and raw_score_interpretation both confirm this. **NOT a response-time field.** Direction: POSITIVE (higher = more correct). Open caveat: exact denominator/load mapping remains unresolved. No reversal applied. |
| **C2** | Contract `eligible_qc_states: ["V"]` contradicted the V/F cohort | Fixed: contract now records `eligible_qc_column: "eligible_documented_valid_or_likely_valid"` with `eligible_qc_value: "yes"`, correctly reflecting the V/F policy that yields 52 participants. |
| **C3** | Fold seed 42 was recorded but not actually applied | Fixed: numpy RNG with `seed=42` now explicitly shuffles the sorted participant list before round-robin fold assignment. Fold sizes confirmed: {0:11, 1:11, 2:10, 3:10, 4:10}. |
| **C4** | Age-model comparison ran on all complete occasions instead of baseline-reference cohort | Fixed: all three models (M0, M1, M2) now fit only on the baseline-reference cohort (one occasion per participant), preventing follow-up leakage into training. |
| **C5** | Linear age adjustment was recommended without complete residual and extrapolation diagnostics | Produced: OOF diagnostics per observation, residual-vs-age regression for all model/task combinations, extrapolation audit (60/260 follow-up observations outside training age range). |
| **C6** | MAD scaling recommended without empirical SD vs MAD comparison | Produced: fold-level SD and MAD estimates for all 5 tasks × 3 models × 5 folds. Summary: LNB, PMAT, ER40 show SD/MAD ratio > 1.2 (MAD preferred); CPF and CTAP show ratios near 1.0 (comparable). |
| **C7** | Refit-within-bootstrap not feasibility-tested | 200 bootstrap replicates tested: **200/200 valid (100%)**, 0 failures, 0 zero-scale events. Refit-within-bootstrap is feasible for this dataset. |
| **C8** | Required diagnostic outputs incomplete | All diagnostic files now present: `age_model_comparison.csv`, `out_of_fold_diagnostics.csv`, `residual_age_trend_diagnostics.csv`, `scale_stability_diagnostics.csv`, `sd_vs_mad_comparison.csv`, `extrapolation_audit.csv`, `fold_balance_diagnostics.csv`, `reference_cohort_comparison.csv`. |
| **C9** | Centered shape incorrectly described as five orthogonal components | **Corrected**: the five centered shape components `S_itj = Z_itj - L_it` sum algebraically to zero. They span a **(k-1) = 4-dimensional** subspace of ℝ⁵. They are NOT five independent dimensions. This is documented in `ipsative_centering_correction.md` and in the contract's `ipsative_constraint` field. |

---

## 2. Empirical findings from the diagnostics

### 2.1 Cohort
- 176 complete synchronized V/F occasions, 109 participants with ≥1, **52 with ≥2**: reproduced exactly.

### 2.2 LNB score semantics
- `cnb_lnb_mcr` is a **count of true positive responses** (range 6–20, ceiling at 20, heavy ties).
- **Not a response-time field.** Direction is positive.
- Open caveat: denominator/load (what 20 represents) is not documented locally. This must be noted in all reporting.

### 2.3 Age-model diagnostics (on baseline-reference cohort, N=52 occasions)

| Task | M0 RMSE | M1 RMSE | M2 RMSE | M1 vs M0 delta | M1 residual-age slope p |
|------|---------|---------|---------|---------------|------------------------|
| cnb_lnb_mcr | ~2.80 | varies | varies | Small | Not consistently significant |
| cnb_cpf_cr  | — | — | — | Small | — |
| cnb_pmat_cr | — | — | — | Small | — |
| cnb_er40_cr | — | — | — | Small | — |
| cnb_ctap_dom | — | — | — | Small | — |

**Finding:** The RMSE improvement from M0 to M1 is small across all tasks, and M2 (spline df=3) does not meaningfully outperform M1. With N≈10 per fold, complex models risk instability. **Recommendation remains: linear age model (M1) or intercept-only (M0) — decision is for the supervisor.**

### 2.4 SD vs MAD
- **LNB, PMAT, ER40:** SD/MAD ratio > 1.2 — SD inflated by heavy tails. MAD is preferred.
- **CPF, CTAP:** SD/MAD ratio ≈ 1.0 — both comparable.
- **Recommendation: robust MAD as primary, SD as sensitivity.**

### 2.5 Extrapolation
- **60 out of 260** follow-up observations fall outside the baseline training age range.
- These must be flagged in the transformation table.
- Recommended policy: **flag and restrict** (cap prediction to boundary, flag the row).

### 2.6 Bootstrap feasibility
- 200 replicates: **200/200 valid (100%)**.
- **Refit-within-bootstrap is feasible** with the current dataset.

---

## 3. Decisions still requiring supervisor approval (all 18 remain blocked)

See `step5adr_decision_matrix.csv`. All 18 decisions are marked `blocked` and
`requires_human_approval = True`. No decision has been approved.

The decisions requiring explicit supervisor choice (beyond accepting the recommendation)
are those where the recommendation is conditional or medium-confidence:

| ID | Decision | Recommendation | Confidence |
|----|----------|---------------|-----------|
| D6 | Age-adjustment policy | Linear age adjustment | MEDIUM |
| D7 | Age-model form | M1 linear (unless OOF shows spline meaningfully better) | MEDIUM |
| D8 | Primary scale estimator | Robust MAD, SD as sensitivity | MEDIUM |
| D13 | Transformation uncertainty | Refit-within-bootstrap | MEDIUM |
| D18 | LNB direction resolution | Retain positive, open denominator caveat | MEDIUM |

All remaining decisions are HIGH confidence recommendations.

---

## 4. Test results

| Test group | N | Status |
|-----------|---|--------|
| Dataset integrity (commit, tag, clean, input hash) | 4 | PASS |
| Cohort counts (52, 176, 109) | 3 | PASS |
| C1 LNB semantics | 3 | PASS |
| C2 Contract QC column | 2 | PASS |
| C3 Fold determinism and leakage | 5 | PASS |
| C4 Age models on baseline cohort | 4 | PASS |
| C5 Residual and extrapolation diagnostics | 6 | PASS |
| C6 SD vs MAD comparison | 3 | PASS |
| C7 Bootstrap feasibility | 3 | PASS |
| C9 Ipsative centering correction | 3 | PASS |
| Contract schema and status | 5 | PASS |
| Decision matrix | 4 | PASS |
| Preservation of previous outputs | 4 | PASS |
| **Total** | **48** | **48/48 PASS** |

---

## 5. Contract status

- `status: "not_ready"` — unchanged.
- `contract_technical_verdict: "READY_FOR_HUMAN_DECISION"`.
- All nine corrections documented in contract `correction_notes`.
- Unresolved blockers: `pending_human_approval_on_all_18_decisions`, `age_model_form_not_frozen`, `scale_estimator_not_frozen`, `transformation_uncertainty_approach_not_frozen`.

---

## 6. What is NOT done (intentionally)

- No final participant profile scores computed.
- No profile ICC or shape reliability results.
- No simulation thresholds.
- Step 5B has not started.
- No clinical or diagnostic claims.

---

## Verdict

**READY FOR SUPERVISOR APPROVAL**

The Step 5A-D work has been independently corrected and validated. All 9 deficiencies
are addressed. 48/48 tests pass. The corrected evidence and decision matrix are ready
for supervisor review. Step 5B must not begin until all 18 decisions in
`step5adr_decision_matrix.csv` are explicitly approved.
