# CHAVI Master Project Specification and Handoff

**Document type:** Authoritative project handoff and recovery specification
**Updated:** 30 September 2026
**Repository:** `C:\Users\asmi\Desktop\Projects\CHAVI`
**Project status:** Upstream measurement work is reusable; post-transformation outputs are quarantined pending rebuild
**Dataset:** Penn LEAD, OpenNeuro `ds007116`, snapshot/tag `1.0.6`
**Pinned commit:** `fc7dc36fa2598b0b2e4579baef37d148cc085207`

## 0. Read-first operating rule

This document is written for an AI agent taking over without the previous conversation. The most important fact is that the repository contains a completed-looking but non-authoritative transformation branch. Do not infer project completion from directories named `contract_freeze`, `transformed_data`, `independent_review`, or `final_validation`.

The latest read-only forensic audit found a lineage break between the approved transformation intent and its implementation. Therefore:

- the last reusable boundary is Step 5A measurement specification plus Step 5A-D-R2 evidence;
- Step 5A-F is an approval record, not proof of correct implementation;
- Step 5B-A through Step 5B-A-R3 outputs are forensic reference and must be regenerated;
- no profile-level scientific result, simulation result, selective-reporting threshold, baseline comparison, or Evidence Engine result is valid yet.

When documents conflict, use this precedence order:

1. raw pinned dataset and verified source payload hashes;
2. source-row manifests and independently reconstructed cohort manifests;
3. the recovery audit and its issue register;
4. Step 5A-D-R2 evidence;
5. Step 5A-F approval values as intended decisions;
6. later generated tables, reports, and validators only as artifacts to diagnose.

Status labels in this document mean: **verified upstream** = independently reproduced or checked against source; **approved intent** = recorded decision not yet proven in implementation; **quarantined** = retained but not reportable; **planned** = not implemented; **blocked** = must not proceed until named issue is resolved.

## 1. Project identity and research question

CHAVI is an independent, non-diagnostic research framework studying whether individualized longitudinal cognitive-profile claims are sufficiently dependable and uncertainty-aware to be reported responsibly. The intended chain is:

```text
Penn LEAD task audit
  -> task-level longitudinal agreement
  -> synchronized five-task occasions
  -> defensible task coordinate transformation
  -> level/elevation, scatter, and shape
  -> uncertainty and mechanical-instability analysis
  -> known-truth simulation
  -> calibrated Report / Caution / Refuse rule
  -> transparent baseline comparison
  -> offline auditable Evidence Engine
```

The framework-level question is:

> Can a simulation-calibrated, uncertainty-aware selective-reporting rule reduce unsupported claims about persistent individualized cognitive-profile features compared with simpler reporting strategies, while retaining useful reporting coverage?

The current empirical question is narrower:

> After separating profile elevation, scatter, and relative shape, how dependable are individual five-measure profile features, and how much observed shape instability is mechanically expected from measurement error and centering?

CHAVI must not diagnose ADHD, autism, psychosis, or any other condition; establish clinical impairment; produce population norms; label a person’s permanent strengths or weaknesses; or claim that a single task represents a validated cognitive domain.

## 2. Dataset and provenance

| Property | Verified value or boundary |
|---|---|
| Dataset | Penn LEAD / OpenNeuro `ds007116` |
| Release | tag `1.0.6` |
| Commit | `fc7dc36fa2598b0b2e4579baef37d148cc085207` |
| DOI in metadata | `10.18112/openneuro.ds007116.v1.0.6` |
| License in metadata | CC0 |
| Registered participants | 132 |
| Recorded session rows | 225 |
| Participants with 1 / 2 / 3+ recorded visits | 59 / 53 / 20 |
| Phenotype payloads | 41/41 retrieved and verified against Git-annex keys |
| Broad cognitive participant-session keys | 219 across 131 source participants |
| Candidate repeated cognitive participants | 70 before the five-task complete-profile restriction |

The local dataset repository must remain pinned and clean. Git-annex pointer files are not the materialized phenotype payloads; the retrieved payloads were staged and hash-checked separately. Do not edit or repoint the dataset checkout.

The sample is longitudinal but not a short-interval retest sample. Visit timing is long and rounded/anonymized. Development, practice, context, administration, real change, and measurement error are confounded. The results must be called longitudinal agreement or dependability, not pure test-retest reliability.

The current study does not require MRI, EEG, gaze, audio/video, deep-learning inputs, new recruitment, or private clinical data. The sample is not a population-norming sample, and study-group labels are recruitment/experimental grouping variables rather than definitive diagnoses.

## 3. Five task measurements

| Order | Task | Field | Direction | Interpretation boundary |
|---:|---|---|---|---|
| 1 | Letter N-back | `cnb_lnb_mcr` | positive | Count of true-positive responses; denominator/load is unresolved, so do not call it normalized accuracy |
| 2 | Penn Face Memory | `cnb_cpf_cr` | positive | Correct-response field; not the whole episodic-memory domain |
| 3 | Penn Matrix Reasoning | `cnb_pmat_cr` | positive | Correct-response field; not the whole complex-cognition domain |
| 4 | Emotion Recognition/ER40 | `cnb_er40_cr` | positive | Correct-response field; not the whole social-cognition domain |
| 5 | Short Computerized Finger Tapping | `cnb_ctap_dom` | positive | Mean dominant-hand trial value; exact unit/aggregation remains a caveat |

No score may be silently age-adjusted, reversed, centered, standardized, combined, or interpreted as a validated domain. The official task context is the Penn CNB Explore Tests page: <https://webcnp.med.upenn.edu/explore-tests.html>.

## 4. Verified upstream work

### 4.1 Steps 1–3B: audit and analysis-data preparation

These stages are reusable, subject to their recorded caveats:

- dataset remote, branch, tag, commit, participant count, session count, file inventory, and provenance were checked;
- all 41 missing phenotype payloads were retrieved and verified against pinned Git-annex size/SHA-256 keys;
- 21 cognitive and 20 questionnaire/outcome tables were audited;
- identifiers were separated from score fields;
- exact QC meanings were used rather than substring matching;
- valid, likely-valid, invalid, skipped, excluded, unresolved, missing, partial, and absent states remain distinct;
- the earlier accidental inclusion of `Not Valid` records was corrected;
- source task observations and pair manifests were generated without imputing scores;
- the five-task feasibility table was reconstructed as 176 eligible complete occasions, 109 participants with at least one, 52 with at least two, and 48 complete scheduled `ses-1`/`ses-2` pairs;
- no standardized scores, composites, fitted age models, ICCs, prediction models, imputations, or Evidence Engine decisions were produced in Step 3B.

The `50 / 52 / 53` reconciliation is important: 53 is the intersection of participants with a separate eligible pair for each task; 50 is the subset whose independently selected task pairs share the same session labels; 52 is the profile-first count obtained by selecting two jointly complete synchronized occasions. The profile-first construction is the candidate basis, but downstream transformation must still be rebuilt correctly.

### 4.2 Step 4A: Face Memory

Verified and independently reviewed:

| Quantity | Result |
|---|---:|
| Included pairs | 59 |
| ICC(A,1) | 0.560473 |
| Bootstrap 95% CI | [0.343745, 0.718958] |
| ICC(C,1) | 0.564114 |
| Pearson | 0.583156 |
| Spearman | 0.555388 |
| Mean later-minus-earlier | 0.847458 |
| Change bootstrap 95% CI | [-0.372881, 2.034322] |
| Bootstrap repetitions | 5,000 participant-pair resamples; seed `20260914` |

### 4.3 Step 4B: five-task agreement

| Task | Pairs | ICC(A,1) | Bootstrap 95% CI | Mean later-minus-earlier | Change 95% CI |
|---|---:|---:|---|---:|---|
| Letter N-back | 55 | 0.660377 | [0.279099, 0.854655] | 0.000000 | [-0.636364, 0.618182] |
| Face Memory | 59 | 0.560473 | [0.343745, 0.718958] | 0.847458 | [-0.372881, 2.034322] |
| Matrix Reasoning | 57 | 0.747309 | [0.564967, 0.850316] | 0.228070 | [-0.526316, 1.017982] |
| Emotion Recognition | 58 | 0.272176 | [0.123102, 0.527584] | 1.844828 | [0.896552, 2.965517] |
| Dominant Finger Tapping | 57 | 0.463781 | [0.315853, 0.583780] | 4.795322 | [2.841959, 6.836257] |

All 286 reconstructed task pairs matched the Step 4B output; its independent review recorded 80 statistical crosschecks and 25 bootstrap metric audits. These are task-level descriptive agreement results. They do not prove practice effects, causality, static traits, or individual-level reportability.

### 4.4 Step 5A: synchronized profile specification

Verified candidate counts:

| Stage | Count |
|---|---:|
| Registered participants | 132 |
| Participants represented in task sources | 131 |
| Complete synchronized V/F occasions | 176 |
| Participants with at least one | 109 |
| Participants with two jointly complete occasions | 52 |

Step 5A defined the intended distinctions among elevation/level, scatter/differentiation, and centered relative shape. It also documented ipsative dependence: five centered components sum to zero, so they occupy a four-dimensional subspace and are not five independent outcomes. It specified sensitivity analyses, missingness rules, uncertainty questions, and mechanical-instability simulations, but did not generate authoritative profile estimates.

### 4.5 Step 5A-D-R2: final pre-transformation evidence

The R2 package evaluated two reference cohorts, age models, SD versus MAD scaling, age support/extrapolation, LNB semantics, and 1,000 bootstrap-feasibility replicates. Its evidence was used to record intended decisions:

- primary synchronized cohort: 52 participants with two complete V/F occasions;
- Reference A: 109 participants’ earliest complete synchronized occasion;
- M0 no-age-adjustment primary; linear M1 sensitivity; spline M2 excluded from primary;
- MAD primary with SD sensitivity under the recorded heavy-tail rule;
- no imputation;
- retain extremes with leave-one-out influence diagnostics;
- refit transformation inside bootstrap when feasible;
- primary estimand intended as mean of five transformed task coordinates;
- centered shape and scatter secondary; profile correlation descriptive only;
- LNB positive true-positive count with unresolved denominator.

R2 is evidence and decision support. It is not authorization to trust the later transformed tables.

## 5. Contract record versus implementation truth

`chavi_analysis_ds007116_step5af_contract_freeze_20260916/` contains `SUPERVISOR_APPROVAL.yaml` and `step5af_transformation_contract_frozen.json`. These record an intended frozen contract, including Reference A = 109, five grouped folds with seed 42, M0 primary, MAD primary, M1 sensitivity, P3 extrapolation handling, no imputation, and a 5,000-valid-bootstrap target.

The recovery audit found that the later artifacts do not establish that this contract was implemented. The decisive contradiction is reference fitting:

- 109 Reference A participants × 5 tasks = 545 reference rows;
- five folds must have held-out sizes 22, 22, 22, 22, 21;
- corresponding training-reference sizes must be 87, 87, 87, 87, 88;
- artifacts reporting 98/99 or 41/42 training participants cannot be accepted as the same implementation;
- 41/42 is consistent with fitting the 52-person primary cohort and is wrong for Reference A.

There is a second contract gap: the frozen JSON did not explicitly define M1 residual scale and support semantics. Later R3 artifacts added M1 behavior without a clean contract amendment chain. A rebuild must resolve and hash this field before execution.

## 6. Recovery audit findings

The latest audit is in `chavi_recovery_phase1_forensic_audit_20260916/`. Its verdict is read-only and no prior artifact was modified.

| ID | Severity | Finding | Required treatment |
|---|---|---|---|
| CHAVI-001 | Critical | Reference A = 109 conflicts with later 41/42-person fitting evidence | Regenerate authoritative transformation |
| CHAVI-002 | Critical | M1 scale/support semantics missing from frozen JSON and added later without clean lineage | Reconstruct/amend contract before code |
| CHAVI-003 | High | 120/206-row wide tables mix Primary and V-only metadata | Quarantine and regenerate with explicit keys |
| CHAVI-004 | High | 540/970 rows use different denominators and are described ambiguously | Report row, occasion, participant, and stratum denominators separately |
| CHAVI-005 | High | Validators reuse production outputs/helpers or copied code | Write genuinely independent source-reconstruction validator |
| CHAVI-006 | High | 55/60/70/75/140 extrapolation counts have changing denominators | Recompute from stable participant/task keys |
| CHAVI-007 | Medium | Reports and CSV semantics do not always align | Reconcile claims, reports, and manifests |
| CHAVI-008 | Medium | Root scratch/validator/engine scripts compete with milestone code | Document lineage; do not treat root scripts as canonical pipeline |

The audit’s trusted-boundary recommendation is explicit: reuse Step 5A and R2 upstream evidence, reuse Step 5A-F only as an approval record, and regenerate all Step 5B-A through R3 transformed tables, parameters, wide tables, M1/extrapolation outputs, reports, and validation claims.

## 7. Required rebuild specification

Create a new dated directory. Do not edit the old transformation directories. The rebuild must include at minimum:

```text
step5ba_rebuild_specification.json
reference_cohort_manifest.csv
participant_fold_manifest.csv
primary_vf_source_rows.csv
vonly_source_rows.csv
transformation_parameters.csv
transformed_task_observations_long.csv
transformed_profiles_wide.csv
support_and_extrapolation_audit.csv
claims_register.csv
provenance.json
independent_validator.py
test_rebuild.py
reproduction_and_review.md
```

### 7.1 Inputs

Use the verified Step 3B source task table and synchronized occasion/pair manifests. Verify their hashes before execution. Do not use the existing transformed long/wide tables as inputs. Record the dataset commit, source hashes, Python version, package versions, command, seed, and Git status.

### 7.2 Cohort and strata

The primary V/F analysis has 52 participants and exactly two synchronized complete occasions each. The V-only sensitivity has 45 participants and two occasions each. Their union may contain 194 participant-stratum-occasion records, but it must not be represented as one canonical cohort. Every row must include `analytical_stratum` and preserve source participant/session keys.

Reference A has 109 participants, one earliest complete synchronized occasion per participant, and 545 task rows. Reference B is a 52-participant sensitivity reference only.

### 7.3 Folds and fitting

Sort the 109 Reference-A participant IDs deterministically, apply the frozen seed 42 permutation, and assign round-robin to five participant folds. Keep all occasions of a participant in the same fold. For each held-out participant, fit only on the other Reference-A participants in that fold. Emit fold membership and training IDs, not only counts.

For every task and coordinate type, record center, scale, model form, support bounds, training IDs/hash, and parameter hash. The independent validator must recompute these from source rows and must not import the production parameter CSV or copied production helper functions.

### 7.4 Coordinates and support

The intended M0 primary coordinate is conceptually:

```text
Z_itj = direction_j * (X_itj - fitted_center_j) / fitted_scale_j
```

The exact scale, fold application, zero-scale refusal, M1 residual definition, and support/extrapolation semantics must be explicit in the rebuilt contract. No-age M0 is not itself age-extrapolated. An age-adjusted M1 coordinate outside its fold-specific support must follow the approved explicit fallback/unsupported rule; it must never inherit an M1 support flag merely because a row exists in the M0 output.

### 7.5 Wide and long outputs

Long output must have exactly one row per source task key plus explicit stratum/model metadata. Wide output must have one row per unique participant-stratum-occasion key and exactly five task coordinate columns. Do not pivot on nonconstant metadata without checking the key. Publish separate primary, V-only, and intentionally combined tables; never silently merge them.

### 7.6 Independent validation gates

Before declaring the rebuild usable, an independent validator must verify from source data:

1. 109 reference participants and 545 reference rows;
2. expected fold identities and training sizes 87/87/87/87/88;
3. 52×2×5 primary rows and 45×2×5 V-only rows;
4. no duplicate participant/stratum/session/task keys;
5. no held-out participant in its training reference;
6. exact direction and LNB metadata;
7. independently recomputed centers, scales, predictions, residuals, and coordinates;
8. zero-scale and missing-age behavior;
9. M1 support/extrapolation counts reconciled by stable participant/task keys;
10. deterministic rerun hashes;
11. no changes to earlier milestone files;
12. report and claims-register denominators equal the CSV semantics.

Only after all gates pass may the rebuilt transformed data be used for profile-level analysis.

## 8. Future analytical stages after rebuild acceptance

### Stage 1: profile measurement

Estimate level/elevation as the mean of five coordinates, scatter as a prespecified differentiation summary, and centered relative shape as a four-dimensional dependent representation. Keep shape correlation descriptive because five-task profile correlations can be unstable. Carry transformation uncertainty through participant-level bootstrap where feasible.

### Stage 2: mechanical-instability analysis

Simulate or analytically characterize the instability expected from imperfect reliability, correlated task errors, centering, discrete scores, and the selected scaling rule. Distinguish observed instability from mathematically induced instability.

### Stage 3: known-truth simulation

Use ADEMP: Aims, Data-generating mechanisms, Estimands, Methods, Performance measures. Keep training/calibration scenarios separate from held-out evaluation scenarios. Vary true-score covariance, correlated error, common shifts/practice, missingness, cohort size, and task reliability. Report Monte Carlo uncertainty and failed/undefined replicates.

### Stage 4: selective reporting and baselines

Calibrate Report/Caution/Refuse thresholds only on training scenarios. Evaluate on held-out scenarios at matched coverage against transparent baselines. Do not tune thresholds on evaluation data and do not claim empirical population validity from simulation alone.

### Stage 5: Evidence Engine

The future engine must be offline and auditable. It should display frozen inputs, evidence, decision, reason codes, uncertainty, limitations, and provenance. It must not recalculate hidden alternative statistics in the UI or use an LLM to make scientific decisions.

## 9. Scope boundaries and forbidden claims

Included in the first complete study: Penn LEAD task dependability; synchronized five-measure profile; level/scatter/shape; uncertainty and sensitivity; known-truth simulations; selective-reporting calibration; transparent baselines; offline Evidence Engine; reproducible report.

Out of scope for the current core: ADHD/ASD classification; clinical diagnosis; treatment recommendations; child-facing deployment; deep learning; MRI/EEG/gaze analyses; generic upload-any-dataset claims; cloud deployment; universal CHAVI score; predictive validity as a primary objective; and LLM-generated scientific decisions.

Do not claim:

- five validated cognitive domains;
- population or clinical z-scores;
- normalized LNB accuracy;
- confirmed practice effects or causal development;
- individual clinical strengths/weaknesses;
- stable trait status from long-interval agreement;
- prediction accuracy for an external outcome;
- reportability before simulation calibration and held-out evaluation.

## 10. Repository map

| Path | Role |
|---|---|
| `ds007116/` | Pinned source dataset checkout; never edit |
| `chavi_analysis_ds007116_step1b_...` through `step4b_...` | Audit, retrieval, QC, preparation, and verified task-level work |
| `chavi_analysis_ds007116_step5a_measurement_specification_20260916/` | Last reusable measurement specification |
| `chavi_analysis_ds007116_step5adr2_final_review_20260916/` | Last reusable pre-transformation evidence review |
| `chavi_analysis_ds007116_step5af_contract_freeze_20260916/` | Approval record; not implementation proof |
| `chavi_analysis_ds007116_step5ba_transformed_data_20260916/` | Quarantined first transformation branch |
| `chavi_analysis_ds007116_step5bar2_independent_review_20260916/` | Quarantined review branch |
| `chavi_analysis_ds007116_step5bar3_final_validation_20260916/` | Quarantined R3 branch; exposes contract/denominator conflicts |
| `chavi_recovery_phase1_forensic_audit_20260916/` | Latest forensic audit and trusted-boundary decision |
| `recovery_phase1_audit.py` | Read-only recovery audit script |
| `independent_transformation_validator.py` | Root validator flagged by audit as not independent; do not treat as proof |
| `step5bar3_engine.py` | Root transformation-related script; noncanonical until lineage is resolved |
| `scratch_validation.py` | Undocumented scratch script; not canonical |

## 11. Exact handoff instruction

The next agent must:

1. read this file and `summary.md`;
2. read the recovery report, trusted-boundary recommendation, issue register, fold expectations, and lineage/independence review;
3. verify the pinned dataset and source hashes;
4. reconstruct a new transformation contract with explicit M1 semantics;
5. regenerate the transformation package in a new directory;
6. run a genuinely independent source-based validator;
7. reconcile every participant, occasion, task, stratum, and extrapolation denominator;
8. stop for supervisor review if any gate fails;
9. only then begin profile-level estimands.

Do not start simulation, selective-reporting calibration, prediction, or UI work while CHAVI-001 through CHAVI-006 remain unresolved.
