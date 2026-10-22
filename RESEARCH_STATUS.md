# CHAVI Research Status

**Evidence snapshot:** 1 October 2026  
**Research stage:** task-level empirical agreement is complete; profile-coordinate construction is not yet accepted.

## Research problem

CHAVI studies when persistent-looking features of an individual's longitudinal cognitive-task profile are dependable enough to report. The core contribution is intended to be a transparent chain from measurement evidence through known-truth simulation to selective reporting, with explicit uncertainty and refusal when evidence is inadequate.

The current dataset-specific question is narrower: after separating overall level, scatter, and centered shape across five tasks, how dependable are those profile features, and how much apparent shape instability is mechanically induced by task unreliability, correlated error, scaling, discreteness, and ipsative centering?

## Proposed approach

1. Audit task scores, QC states, occasions, missingness, and provenance.
2. Quantify task-level longitudinal agreement.
3. Build synchronized complete five-task occasions.
4. Transform heterogeneous task scores into explicit internal coordinates using cross-fitted reference parameters.
5. Estimate profile level, scatter, and shape with transformation uncertainty.
6. quantify mechanical instability expected under measurement error.
7. Run ADEMP known-truth simulations.
8. Calibrate Report/Caution/Refuse thresholds on training scenarios only.
9. Compare with transparent baselines at matched reporting coverage on held-out scenarios.
10. Expose frozen evidence, decisions, uncertainty, reason codes, and provenance in an offline Evidence Engine.

Steps 1–3 are complete. Step 4 has attempted implementations but no accepted result. Steps 5–10 are not implemented authoritatively.

## Dataset

**COMPLETED / VERIFIED:** Penn LEAD/OpenNeuro `ds007116`, version `1.0.6`, commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`, 132 registered participants and 225 session rows. Forty-one phenotype payloads were retrieved separately and verified against annex hashes.

The analysis uses five Penn CNB task fields: `cnb_lnb_mcr`, `cnb_cpf_cr`, `cnb_pmat_cr`, `cnb_er40_cr`, and `cnb_ctap_dom`. It does not presently use MRI, EEG, gaze, audio/video, or deep learning.

## Cohorts and preprocessing

**COMPLETED / VERIFIED:**

- broad cognitive participant-session keys: 219 across 131 source participants;
- candidate repeated cognitive participants before five-task restriction: 70;
- complete synchronized V/F occasions: 176;
- participants with at least one complete synchronized occasion: 109;
- participants with two jointly complete occasions: 52;
- primary source trace: 52 × 2 × 5 = 520 task rows;
- V-only sensitivity cohort: 45 participants, intended 45 × 2 × 5 = 450 rows;
- no primary imputation;
- exact QC categories retained rather than collapsed.

The 50/52/53 discrepancy is reconciled: 53 is the intersection of participants with a task-specific pair for each task; 50 share the same selected session labels across those task pairs; 52 arise from the profile-first synchronized-occasion construction.

## Task-level experiments and findings

**COMPLETED / VERIFIED:** Face Memory Step 4A and five-task Step 4B used participant-pair resampling with 5,000 bootstrap repetitions per task. Independent reviews reconstructed 286 task pairs and checked formulas, statistics, resampling, intervals, exclusions, plots, and file integrity.

| Task | N pairs | ICC(A,1) | 95% bootstrap CI | Mean change | Change 95% CI |
|---|---:|---:|---|---:|---|
| Letter N-back | 55 | 0.660377 | [0.279099, 0.854655] | 0.000000 | [-0.636364, 0.618182] |
| Face Memory | 59 | 0.560473 | [0.343745, 0.718958] | 0.847458 | [-0.372881, 2.034322] |
| Matrix Reasoning | 57 | 0.747309 | [0.564967, 0.850316] | 0.228070 | [-0.526316, 1.017982] |
| Emotion Recognition | 58 | 0.272176 | [0.123102, 0.527584] | 1.844828 | [0.896552, 2.965517] |
| Dominant Finger Tapping | 57 | 0.463781 | [0.315853, 0.583780] | 4.795322 | [2.841959, 6.836257] |

These estimates are descriptive longitudinal agreement. They do not identify practice effects, development, causality, or permanent individual traits.

## Transformation methodology

**COMPLETED / VERIFIED as decision evidence, not as final implementation:**

- Reference A should be 109 participants' earliest complete synchronized occasion, 545 task rows.
- Primary M0 coordinate is conceptually `direction_j * (X_itj - center_j) / scale_j`.
- M0 no-age adjustment is primary because the prespecified R2 criterion favored M1 for 0/5 tasks.
- M1 linear-age adjustment is sensitivity; M2 spline is excluded.
- MAD is primary and SD sensitivity because 3/5 tasks met the heavy-tail rule and no near-zero MAD event was observed.
- Five participant-grouped folds use seed 42.
- P3 is intended for M1 extrapolation: unsupported age-adjusted coordinate, retain M0.
- Transformation should be refit within participant bootstrap where feasible.
- Five centered shape components sum to zero and occupy a four-dimensional subspace.

**IMPLEMENTED / NOT FULLY VALIDATED:** Existing Step 5B-A/R2/R3 code generated parameters and transformed rows, but it fails the accepted lineage/independence boundary. No transformation table is currently reportable.

## Intended profile estimands

**PLANNED / NOT IMPLEMENTED authoritatively:**

- Level/elevation: mean of five task coordinates.
- Centered shape: each coordinate minus occasion level; algebraically dependent in a four-dimensional subspace.
- Scatter: root mean square of centered coordinates.
- Shape change: RMSE between centered occasion vectors.
- Profile correlation: descriptive only because five-element correlations are unstable.
- Conditional SEM/MDC: descriptive with an explicit static-true-score caveat.

No accepted numerical values, ICCs, confidence intervals, SEM/MDC estimates, or individual classifications exist for these estimands.

## Validation status

Historical tests and reviews exist at every stage. Their evidential weight differs:

- Step 4A/4B source reconstruction is accepted as task-level verification.
- Step 5A and R2 counts/diagnostics are accepted as upstream evidence.
- Step 5B/R2/R3 tests are not independent enough to validate transformation correctness.
- The current environment cannot rerun the suites because required packages and `pytest` are absent.

## Research gaps and limitations

### BLOCKED

- A clean transformation contract must explicitly define M1 residual scaling, fold-specific support, extrapolation, fallback, and parameter lineage.
- Reference-A folds must train on 87/87/87/87/88 participants, not 98/99 or 41/42.
- Primary, V-only, canonical-union, and stratified denominators must be represented with stable keys.
- A genuinely independent validator must reconstruct source rows and recompute parameters/coordinates without production artifacts or copied helpers.

### UNKNOWN / REQUIRES CONFIRMATION

- exact LNB denominator/load mapping;
- exact CTAP unit/aggregation semantics;
- task-version equivalence across the long interval;
- whether the approved M1 interpretation will be formally amended or refrozen;
- external generalizability beyond this sample.

### Structural limitations

- N=52 for the primary longitudinal profile cohort is small.
- Visit intervals are long, rounded/anonymized, and nonuniform.
- Complete-case selection and V/F policy can induce selection differences.
- Discrete scores, ceiling/ties, heavy tails, and centering can mechanically create apparent instability.
- Reference A is an internal sample, not a population norm.
- Simulation can establish operating characteristics under specified data-generating mechanisms, not empirical clinical validity.

## Planned research not yet implemented

1. Accepted transformed coordinate rebuild.
2. Profile-level level/scatter/shape estimation and uncertainty.
3. Leave-one-participant-out influence analysis.
4. Mechanical-instability analysis.
5. ADEMP simulation with separated calibration and held-out evaluation scenarios.
6. Report/Caution/Refuse threshold calibration.
7. Matched-coverage baseline comparison with Monte Carlo uncertainty.
8. Offline auditable Evidence Engine.
9. Paper and reproducibility package.

## Current research conclusion

The strongest scientific contribution currently supported is a carefully audited five-task longitudinal measurement dataset plus verified task-level agreement results and a detailed, but not yet successfully implemented, profile-transformation specification. It is premature to make claims about profile stability, individual reportability, selective-reporting performance, or clinical usefulness.

