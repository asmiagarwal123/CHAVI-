# CHAVI Agent Handoff Summary

**Updated:** 30 September 2026
**Repository:** `C:\Users\asmi\Desktop\Projects\CHAVI`
**Project:** CHAVI — a non-diagnostic, reproducible study of whether individualized longitudinal cognitive-profile claims are dependable enough to report.

## Read this first

The project is **not cleared to use any transformed profile table, profile reliability result, simulation result, reporting threshold, or Evidence Engine result**. The latest forensic recovery audit found a lineage break in the post-transformation artifacts. The last reusable scientific boundary is:

1. the Step 5A measurement specification; and
2. the Step 5A-D-R2 final evidence review, limited to independently reproducible upstream cohort evidence.

The Step 5A-F approval files remain useful as a record of intended decisions, but they do not prove that the later implementation correctly applied those decisions. Step 5B-A, Step 5B-A-R2, and Step 5B-A-R3 outputs are **forensic reference only** until regenerated from a repaired specification.

## Current status

| Area | Status | Meaning |
|---|---|---|
| Dataset identity and provenance | Verified | Penn LEAD/OpenNeuro `ds007116`, tag `1.0.6`, commit `fc7dc36fa2598b0b2e4579baef37d148cc085207` |
| Phenotype retrieval and source audit | Verified | 41/41 Git-annex phenotype payloads retrieved and hash-checked |
| Exact score/QC policy | Verified with caveats | Valid and likely-valid records are distinguished; invalidity overrides missing/unresolved QC |
| Step 3B analysis data | Verified upstream | Long task table, pair manifests, and synchronized-profile candidates exist |
| Step 4A Face Memory agreement | Verified and independently reviewed | 59 pairs; ICC(A,1)=0.560473; bootstrap CI [0.343745, 0.718958] |
| Step 4B five-task agreement | Verified and independently reviewed | Task-level results are reusable as narrow longitudinal agreement evidence |
| Step 5A synchronized profile cohort | Verified as candidate | 176 complete synchronized occasions; 109 with at least one; 52 with two |
| Step 5A-D-R2 decisions | Evidence available; not a safe implementation boundary | Reference-A and diagnostic evidence can be reused, but later application must be rebuilt |
| Step 5A-F contract | Approval record only | Intended values are recorded, but the implementation lineage is not trusted |
| Step 5B-A through R3 | Not authoritative | Regenerate; do not cite as final results |
| Profile estimands | Not run authoritatively | No trustworthy level/shape/scatter estimates exist |
| Simulation/calibration/baselines/UI | Not started | Must wait for repaired empirical transformation and review |

## Immediate next action

Create a new non-destructive recovery milestone, for example:

```text
chavi_analysis_ds007116_step5ba_rebuild_20260930/
```

Reconstruct the transformation specification from the trusted Step 5A-D-R2 evidence plus the Step 5A-F approval record, explicitly resolving the missing M1 semantics. Then regenerate every transformed artifact from source inputs. Do not patch or overwrite the old Step 5B directories.

The rebuild must prove, before any profile analysis:

- Reference A contains 109 participants and exactly 545 earliest complete synchronized task rows.
- Five participant folds have held-out sizes 22, 22, 22, 22, and 21, with training-reference sizes 87, 87, 87, 87, and 88.
- No fold fits parameters from the held-out participant.
- The primary V/F stratum is 52 participants × 2 occasions × 5 tasks = 520 task rows.
- The V-only sensitivity stratum is 45 participants × 2 occasions × 5 tasks = 450 task rows.
- Primary, V-only, and any union/stratified table use explicit `analytical_stratum` keys and are never silently deduplicated.
- M0, M1, scale, support, extrapolation, and fallback semantics are machine-readable and identical between code, contract, manifests, and reports.
- An actually independent validator reconstructs source rows and recomputes parameters and coordinates without reading production parameters or copied helpers.

Do not begin profile-level inference until the rebuilt package is independently validated and reviewed.

## Scientific direction

CHAVI asks whether a simulation-calibrated, uncertainty-aware selective-reporting rule can reduce unsupported claims about persistent individualized cognitive-profile features compared with transparent baselines at matched reporting coverage. It is not a diagnostic system, clinical assessment, population norm, classifier, treatment recommender, or general-purpose upload-any-dataset product.

The five task fields are:

| Task | Field | Current interpretation |
|---|---|---|
| Letter N-back | `cnb_lnb_mcr` | True-positive response count; positive direction retained; denominator unresolved |
| Penn Face Memory | `cnb_cpf_cr` | Correct responses |
| Penn Matrix Reasoning | `cnb_pmat_cr` | Correct responses |
| Emotion Recognition/ER40 | `cnb_er40_cr` | Correct responses |
| Dominant Finger Tapping | `cnb_ctap_dom` | Mean dominant-hand trial value; exact unit/aggregation remains a caveat |

These are five task measurements, not five validated cognitive domains. Use “longitudinal agreement” or “dependability,” not pure short-interval test-retest reliability, because the intervals are long, rounded/anonymized, and confounded by development, practice, context, administration, and real change.

## Verified task-level results

These results are prior to profile transformation and remain the strongest completed empirical results:

| Task | Pairs | ICC(A,1) | Bootstrap 95% CI | Mean later−earlier |
|---|---:|---:|---|---:|
| Letter N-back | 55 | 0.660377 | [0.279099, 0.854655] | 0.000000 |
| Face Memory | 59 | 0.560473 | [0.343745, 0.718958] | 0.847458 |
| Matrix Reasoning | 57 | 0.747309 | [0.564967, 0.850316] | 0.228070 |
| Emotion Recognition | 58 | 0.272176 | [0.123102, 0.527584] | 1.844828 |
| Dominant Finger Tapping | 57 | 0.463781 | [0.315853, 0.583780] | 4.795322 |

Each task used 5,000 participant-pair bootstrap repetitions. The change estimates are descriptive and do not establish practice, development, intervention, or causality.

## What happened in the failed post-transformation branch

The frozen approval record intended Reference A to be the 109 participants’ earliest complete synchronized occasion. That implies 545 reference task rows. The recovery audit found that competing later implementations contain incompatible fitting evidence: some parameter artifacts imply training on 98/99 participants, while other artifacts imply fitting on the 52-person longitudinal cohort (training sizes 41/42). A 52-person fit cannot implement Reference A.

The later branch also contains mixed and denominator-dependent tables:

- a 120-row wide artifact mixes Primary and V-only metadata;
- 540 rows represent 108 occasions × 5 tasks;
- 520 rows are the primary V/F stratum;
- 450 rows are the V-only stratum;
- 970 rows are a combined stratified task table, not a canonical single cohort;
- extrapolation counts vary because the denominator and model/stratum differ.

Passing tests in that branch are self-consistency checks, not independent verification: the forensic audit found validators that read production outputs, reuse production parameters, or share copied helpers. The old outputs must be retained for auditability but not used as scientific results.

## Authoritative evidence map

Start with the root [CHAVI_MASTER_PROJECT_SPECIFICATION_AND_HANDOFF.md](CHAVI_MASTER_PROJECT_SPECIFICATION_AND_HANDOFF.md), then inspect:

1. `chavi_analysis_ds007116_step5a_measurement_specification_20260916/` — measurement specification, cohort flow, estimands, missingness, uncertainty, and source traces.
2. `chavi_analysis_ds007116_step5adr2_final_review_20260916/` — final pre-transformation evidence review; reusable for upstream decisions and diagnostics.
3. `chavi_analysis_ds007116_step5af_contract_freeze_20260916/` — approval record and intended contract; not sufficient evidence of implementation correctness.
4. `chavi_recovery_phase1_forensic_audit_20260916/` — latest authority on conflicts, trust boundary, expected fold sizes, artifact variants, lineage, and required recovery.
5. `chavi_analysis_ds007116_step5ba_transformed_data_20260916/`, `step5bar2`, and `step5bar3` — quarantined forensic reference only.

Important recovery files:

- `RECOVERY_PHASE1_FORENSIC_AUDIT_REPORT.md`
- `trusted_boundary_and_recovery_recommendation.md`
- `MASTER_ISSUE_REGISTER.csv`
- `reference_a_fold_expected_counts.csv`
- `reference_a_implementation_comparison.csv`
- `transformed_artifact_variant_comparison.csv`
- `validation_independence_classification.csv`
- `wide_table_row_discrepancy_analysis.csv`

## Reproducibility rules

- Never modify `ds007116`; verify tag, commit, remote, and Git status before use.
- Work in a new dated milestone directory and never overwrite prior outputs.
- Use source task observations and explicit manifests, not derived transformed tables, as rebuild inputs.
- Record hashes before and after each run.
- Preserve participant/session/task keys and every exclusion reason.
- Fit reference parameters only on the declared training reference participants.
- Keep calibration and evaluation scenarios separate in later simulation work.
- Keep primary, QC-sensitivity, and stratified datasets separate with explicit stratum keys.
- Do not impute the primary five-task profile unless a future approved protocol says so.
- Do not silently winsorize, discard extremes, or treat undefined estimates as zero.
- Add tests for cohort counts, fold identities, leakage, formulas, determinism, support flags, and denominator invariants.
- Treat a passing test suite as evidence only when the test has independent source reconstruction.
- Stop at phase boundaries for supervisor review.

## Deferred work

After the repaired transformation package is accepted: estimate elevation/level, scatter, and shape with uncertainty; quantify mechanical instability from centering and measurement error; implement known-truth ADEMP simulations; calibrate Report/Caution/Refuse; compare transparent baselines at matched coverage; build the offline Evidence Engine; and prepare the paper/reproducibility package. None of those downstream claims currently exist.
