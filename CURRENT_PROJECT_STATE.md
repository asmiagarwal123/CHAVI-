# CHAVI Current Project State

**Snapshot date:** 1 October 2026  
**Exact stage:** pre-transformation evidence and approval are available, but no accepted Step 5B transformation implementation exists.

## COMPLETED / VERIFIED

- Dataset identity: OpenNeuro `ds007116`, tag `1.0.6`, commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`, clean dataset Git checkout.
- Dataset/session inventory: 132 registered participants, 225 session rows, 59/53/20 participants with 1/2/3+ visits.
- Forty-one phenotype payloads staged and verified against Git-annex hashes.
- Exact score/QC auditing through Steps 1B–3A, including correction of the `Not Valid` handling defect.
- Step 3B source task/outcome tables, task/profile pair manifests, candidate cohorts, SAP draft, and provenance.
- Step 4A Face Memory longitudinal agreement and source-based independent review.
- Step 4B five-task longitudinal agreement and independent review; 286 pairs reconciled.
- Step 5A synchronized-cohort reconstruction: 176 complete occasions, 109 participants with at least one, 52 with two.
- Step 5A profile estimand, missingness, uncertainty, sensitivity, and mechanical-instability specifications.
- Step 5A-D-R2 diagnostics comparing reference cohorts, age models, scales, extrapolation policies, and bootstrap feasibility.
- Step 5A-F supervisor approval record for decisions D1–D18.
- Recovery Phase 1 forensic audit and trusted-boundary decision.
- Current dataset Git verification and project artifact re-inventory on 2026-10-01.
- Python source syntax compilation on 2026-10-01.
- Fresh 2026-10-01 upstream test rerun: 43/43 tests passed across Step 4A, Step 4A review, Step 4B, Step 4B review, and Step 5A.

## IMPLEMENTED / NOT FULLY VALIDATED

- Step 5B-A transformation runner and outputs.
- Step 5B-A-R2 expanded/stratified transformation outputs.
- Step 5B-A-R3 M1 restoration, split-stratum tables, validators, and tests.
- Root `independent_transformation_validator.py`, `step5bar3_engine.py`, and related scratch scripts.

All items above are quarantined. They are retained for forensic comparison, not scientific use.

## IN PROGRESS

No active rebuild directory exists. Conceptually, transformation recovery is the next in-progress project objective, but actual implementation has **not started** in the inspected workspace.

## PLANNED / NOT IMPLEMENTED

- New dated Step 5B-A rebuild from source rows.
- Explicit amended/refrozen transformation contract with M1 semantics.
- Independent source-reconstruction validator.
- Accepted profile level/elevation, scatter, centered shape, shape RMSE, profile-correlation, SEM/MDC, or profile reliability results.
- Transformation-uncertainty bootstrap for final estimands.
- Mechanical-instability analysis.
- Known-truth ADEMP simulations.
- Selective Report/Caution/Refuse rule calibration.
- Held-out matched-coverage baseline evaluation.
- Offline Evidence Engine.
- Paper/final reproducibility release.

## BLOCKED

| Blocker | Effect | Resolution required |
|---|---|---|
| CHAVI-001: Reference-A fit conflict | All existing coordinates/parameters are non-authoritative | Rebuild 109-person folds with training sizes 87/87/87/87/88 and emitted training identities |
| CHAVI-002: missing M1 contract semantics | M1 sensitivity cannot be independently interpreted | Amend/refreeze model, residual-scale, support, extrapolation, and fallback rules before execution |
| CHAVI-003/004: malformed/mixed wide and denominator semantics | Cohort/occasion identity is ambiguous | Separate Primary (104 occasions), V-only (90), and explicit stratified outputs |
| CHAVI-005: non-independent validation | Green tests give false assurance | Validator must reconstruct source and calculations without production parameters/outputs/helpers |
| CHAVI-006: extrapolation denominator conflict | M1 support counts are not reportable | Reconcile by stable participant/session/task/stratum/model keys |
| Missing runtime dependencies | Tests cannot be freshly executed | Create a declared environment and install compatible scientific packages plus pytest |

## UNKNOWN / REQUIRES CONFIRMATION

- Exact prompt-to-file and author history; root project has no Git metadata.
- Whether any relevant files existed outside this workspace or were deleted before inspection.
- Exact LNB denominator/load mapping.
- Exact CTAP units and aggregation semantics.
- Intended formal approval mechanism for the required M1 contract amendment.
- Whether historical package versions can be recreated exactly; no lockfile exists.

## Current authoritative results

Only task-level agreement results are accepted. No profile-level or selective-reporting result is accepted. See `RESEARCH_STATUS.md` for the full verified table.

## Immediate technical steps

1. Create a reproducible environment declaration; record Python/package versions and verify the historical upstream tests.
2. Read the recovery report, issue register, expected-fold table, contract comparison, transformation variants, and validation-independence table.
3. Draft a new machine-readable rebuild contract; explicitly resolve M1 scale/support/fallback semantics and hash the approval/amendment.
4. Create a new dated directory; never edit old transformation directories.
5. Reconstruct Reference A from Step 3B/Step 5A source rows: 109 participants, one earliest complete synchronized occasion each, 545 task rows.
6. Generate deterministic seed-42 grouped folds and record held-out/training participant IDs.
7. Generate Primary and V-only transformed long/wide outputs with explicit `analytical_stratum` keys.
8. Independently reconstruct and validate centers, scales, predictions, residuals, support flags, coordinates, counts, duplicates, leakage, and deterministic hashes.
9. Stop for review if any gate fails. Only after acceptance proceed to profile estimands.

## Immediate research steps after technical acceptance

1. Estimate level, scatter, and shape with participant-level uncertainty.
2. Run prespecified sensitivities: V-only, SD scaling, Reference B, M1 where supported, influence analyses.
3. Quantify mechanically induced instability.
4. Design and preregister ADEMP simulation before calibrating any reporting threshold.

## Current environment

- Active Python: 3.14.
- Historical environment claim: Python 3.14.0 with pandas 3.0.5, NumPy 2.5.2, SciPy 1.17.0, scikit-learn 1.9.0, statsmodels 0.14.6, matplotlib 3.10.8, seaborn 0.13.2, JupyterLab 4.5.6.
- Current active environment: those scientific packages and `pytest` are absent.
- Standard-library upstream suites remain runnable and passed 43/43; later scientific-stack/pytest suites were not rerun.
- No requirements/lock/environment file was found.
- Multiple scripts contain absolute paths; portability is not yet reliable.
