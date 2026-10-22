# CHAVI ChatGPT/Codex Handoff

**Read this first.** This workspace looks further along than it scientifically is. It contains directories named `contract_freeze`, `transformed_data`, `independent_review`, and `final_validation`, but the accepted boundary is **before transformation implementation**.

## The project in one paragraph

CHAVI is a non-diagnostic research project asking whether individualized longitudinal cognitive-profile features can be reported responsibly using explicit measurement evidence, uncertainty, known-truth simulation, and a selective Report/Caution/Refuse rule. It uses five Penn LEAD/OpenNeuro `ds007116` cognitive task fields. Dataset/QC preparation, synchronized-cohort construction, and task-level agreement are complete. Transformation decision evidence and an approval record exist. The existing transformed-data branch is quarantined because a forensic audit found reference-cohort/fold, contract, denominator, extrapolation, and validation-independence failures. Development must continue with a clean transformation rebuild, not profile analysis or UI work.

## Status labels used here

- **COMPLETED / VERIFIED** — safe to reuse within stated caveats.
- **IMPLEMENTED / NOT FULLY VALIDATED** — artifact exists but is not accepted.
- **IN PROGRESS** — partially executed and awaiting required gates.
- **PLANNED / NOT IMPLEMENTED** — specified only.
- **UNKNOWN / REQUIRES CONFIRMATION** — evidence is absent or conflicting.

## What is safe to trust

**COMPLETED / VERIFIED:**

- `ds007116/` is a clean OpenNeuro checkout at tag `1.0.6`, commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`.
- Forty-one staged phenotype TSVs were verified against annex keys.
- Steps 1B–3B provide audited task/QC/occasion evidence and canonical source observation tables.
- Step 4A/4B task-level agreement is independently reviewed.
- Step 5A establishes 176 complete synchronized V/F occasions, 109 participants with at least one, and 52 with two.
- Step 5A-D-R2 is the last reusable pre-transformation evidence review.
- Step 5A-F is a record of approved intent.
- Recovery Phase 1 is the current authority on what must be quarantined and rebuilt.

## What is not safe to trust

**IMPLEMENTED / NOT FULLY VALIDATED; do not use scientifically:**

- everything in `chavi_analysis_ds007116_step5ba_transformed_data_20260916/`;
- everything in `chavi_analysis_ds007116_step5bar2_independent_review_20260916/`;
- transformation claims in `chavi_analysis_ds007116_step5bar3_final_validation_20260916/`;
- root `independent_transformation_validator.py`, `step5bar3_engine.py`, and `scratch_validation.py`.

Retain these artifacts. They are forensic evidence and should not be deleted or overwritten.

## Required reading order

1. `PROJECT_MASTER_CONTEXT.md`
2. `CURRENT_PROJECT_STATE.md`
3. `chavi_recovery_phase1_forensic_audit_20260916/RECOVERY_PHASE1_FORENSIC_AUDIT_REPORT.md`
4. `chavi_recovery_phase1_forensic_audit_20260916/trusted_boundary_and_recovery_recommendation.md`
5. `chavi_recovery_phase1_forensic_audit_20260916/MASTER_ISSUE_REGISTER.csv`
6. `chavi_recovery_phase1_forensic_audit_20260916/reference_a_fold_expected_counts.csv`
7. `chavi_recovery_phase1_forensic_audit_20260916/reference_a_implementation_comparison.csv`
8. `chavi_recovery_phase1_forensic_audit_20260916/transformed_artifact_variant_comparison.csv`
9. `chavi_recovery_phase1_forensic_audit_20260916/validation_independence_classification.csv`
10. Step 5A, R2, and Step 5A-F specifications/approval.

`CHAVI_MASTER_PROJECT_SPECIFICATION_AND_HANDOFF.md` and `summary.md` are also useful and align with the recovery decision. `chavi_antigravity_handoff_20260916/` is an older snapshot; its statement that Step 5B had not started was later superseded by attempted—but failed—Step 5B work.

## Core data and decisions

Five positive-direction task fields:

| Task | Field | Caveat |
|---|---|---|
| Letter N-back | `cnb_lnb_mcr` | true-positive count; denominator/load unresolved; never call normalized accuracy |
| Face Memory | `cnb_cpf_cr` | correct-response field |
| Matrix Reasoning | `cnb_pmat_cr` | correct-response field |
| Emotion Recognition | `cnb_er40_cr` | correct-response field |
| Finger Tapping | `cnb_ctap_dom` | dominant-hand mean; exact unit/aggregation unresolved |

Approved intent:

- Primary: 52 V/F participants × 2 occasions × 5 tasks = 520 rows.
- V-only sensitivity: 45 × 2 × 5 = 450 rows.
- Reference A: 109 earliest complete occasions × 5 tasks = 545 rows.
- Five participant-grouped seed-42 folds.
- Expected held-out sizes: 22, 22, 22, 22, 21.
- Expected training sizes: 87, 87, 87, 87, 88.
- M0 no-age primary; M1 sensitivity; M2 excluded.
- MAD primary; SD sensitivity.
- No imputation; retain extremes and run leave-one-out influence checks.
- M1 P3 behavior: mark unsupported outside fold-specific age support and use M0.
- Refit transformation within bootstrap if feasibility remains acceptable.
- Level/elevation primary; scatter and shape secondary; profile correlation descriptive.

## Why the old transformation failed

The recovery audit found incompatible fitting evidence. Some parameter files show 98/99 training participants, which is not the approved five-fold 109-person scheme. Other R3 evidence shows 41/42, which is consistent with fitting the 52-person longitudinal cohort and is therefore the wrong reference population. The frozen JSON also omitted a complete M1 residual-scale/support definition; R3 added one without a clean amendment. Wide tables contain 120 or 206 rows where logically separate outputs should contain 104 Primary occasions, 90 V-only occasions, or 194 explicitly stratified records. Extrapolation counts change with denominators. The supposed independent validators reuse production parameters, outputs, or helpers.

## What has already been tried and should not be repeated

- Do not patch the existing 540/970-row transformed tables.
- Do not infer correctness from a 545-row reference manifest alone; parameter training identities/sizes must match the fold contract.
- Do not use a 52-person reference fit while labeling it Reference A.
- Do not pivot a wide table on metadata that are nonconstant within the intended key.
- Do not call 970 stratified rows a single canonical cohort.
- Do not apply age-extrapolation flags to M0.
- Do not add M1 behavior in code without a machine-readable approved contract amendment.
- Do not validate by reading production parameter CSVs or copying production helpers.
- Do not treat passing historical tests as independent scientific validation.
- Do not begin profile ICCs, simulations, threshold calibration, baselines, prediction, or UI work before rebuild acceptance.

## Exact next task

Create a new dated directory, leaving all prior directories unchanged. Before computation, create and approve/hash a rebuild specification that explicitly defines M0 and M1 models, residual scales, folds, support bounds, extrapolation/fallback, zero-scale behavior, stratum keys, output keys, and bootstrap behavior.

Minimum expected files:

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

The production build must start from Step 3B source observations and Step 5A synchronized manifests, verify hashes, preserve keys, emit training identities/hashes, and keep analytical strata explicit.

The independent validator must reconstruct source rows and independently recompute centers, scales, M1 predictions/residuals, coordinates, support flags, duplicates, leakage, denominators, and deterministic hashes. It must not import production helpers or read production parameters as its source of truth.

## Acceptance gates

Do not proceed unless all of these pass:

1. Reference A = 109 participants and 545 unique task rows.
2. Fold identities are deterministic; training sizes are 87/87/87/87/88.
3. No held-out participant appears in its training reference.
4. Primary = 520 rows; V-only = 450 rows.
5. No duplicate participant/stratum/session/task keys.
6. Wide tables are unique by participant/stratum/occasion and contain exactly five task coordinates.
7. Direction/LNB metadata match the approved record.
8. Centers, scales, predictions, residuals, and coordinates independently match source calculations.
9. Zero-scale/missing-age/support behavior follows the amended contract.
10. Extrapolation counts reconcile by stable keys and explicit denominators.
11. Reruns are deterministic and earlier milestone hashes remain unchanged.
12. Reports and claims registers describe the CSV meanings exactly.

## Environment warning

The project has no requirements or lockfile. Historical documentation names Python 3.14.0 and a scientific stack, but the currently active Python lacks `pytest`, NumPy, pandas, SciPy, scikit-learn, statsmodels, and matplotlib. Source compilation succeeds, and 43 standard-library upstream tests across Steps 4A, 4A review, 4B, 4B review, and 5A passed on 1 October 2026. Later scientific-stack/pytest suites were not freshly rerun. Restore and declare the environment before claiming full reproducibility.

Several scripts hard-code absolute paths. Early text references `C:\Users\asmi\Desktop\Projects\ML Projects`; later transformation scripts reference `C:\Users\asmi\Desktop\Projects\CHAVI`. Refactor only in a new milestone or dedicated portability change, preserving historical files.

## Scope boundaries

Never claim diagnosis, clinical validity, population/clinical z-scores, five validated domains, confirmed practice effects, permanent individual strengths/weaknesses, normalized LNB accuracy, external prediction accuracy, or reportability before simulation calibration and held-out evaluation.

## Repository-history warning

The CHAVI root has no `.git`, so project commit/diff history is unavailable. Only the nested dataset is version-controlled. If asked who changed which project file for a particular prompt, answer **UNKNOWN / REQUIRES CONFIRMATION** unless an artifact's own provenance establishes it.
