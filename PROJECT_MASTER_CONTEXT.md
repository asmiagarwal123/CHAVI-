# CHAVI Project Master Context

**Evidence snapshot:** 1 October 2026  
**Workspace:** `C:\Users\asmi\Desktop\Projects\CHAVI`  
**Current authoritative status:** upstream audit, task-level agreement, and pre-transformation measurement work are reusable; all existing Step 5B transformation outputs are quarantined pending a clean rebuild.

## Status vocabulary

- **COMPLETED / VERIFIED** — supported by source artifacts and independent or forensic checks.
- **IMPLEMENTED / NOT FULLY VALIDATED** — code/output exists, but validation is incomplete, non-independent, or contradicted.
- **IN PROGRESS** — active work has artifacts but has not passed its required acceptance boundary.
- **PLANNED / NOT IMPLEMENTED** — specified in documents but no authoritative implementation/result exists.
- **UNKNOWN / REQUIRES CONFIRMATION** — repository evidence is insufficient or conflicting.

## Project purpose and research objective

CHAVI is a non-diagnostic research framework for deciding whether individualized longitudinal cognitive-profile claims are dependable and uncertainty-aware enough to report. Its framework-level question is whether a simulation-calibrated selective-reporting rule can reduce unsupported claims about persistent individual profile features, compared with transparent baselines at matched reporting coverage.

The present empirical work uses Penn LEAD/OpenNeuro `ds007116` to study five longitudinal task measurements. The intended analysis separates:

1. profile level/elevation;
2. within-profile scatter/differentiation; and
3. centered relative shape.

The project must not be described as a diagnostic system, clinical norm, validated five-domain battery, treatment tool, or predictor of a clinical outcome. Long and anonymized visit intervals confound development, practice, context, administration, real change, and measurement error; use **longitudinal agreement** or **dependability**, not pure short-interval test-retest reliability.

## Dataset and provenance

| Item | Evidence-backed state |
|---|---|
| Dataset | Penn LEAD / OpenNeuro `ds007116` |
| Release | `1.0.6` |
| Commit | `fc7dc36fa2598b0b2e4579baef37d148cc085207` |
| DOI | `10.18112/openneuro.ds007116.v1.0.6` |
| License | CC0 |
| Registered participants | 132 |
| Recorded session rows | 225 |
| Participants with 1 / 2 / 3+ visits | 59 / 53 / 20 |
| Phenotype payloads | 41/41 retrieved to separate staging and verified against annex keys |
| Dataset Git state checked 2026-10-01 | clean `main...origin/main`, tag `1.0.6`, expected commit and official remote |
| Project-root Git history | **UNKNOWN / unavailable** — the CHAVI root contains no `.git`; only `ds007116/` is a Git repository |

The raw dataset checkout must not be edited. Imaging and derivative files are present but are outside the current core analysis; the executed CHAVI work is based on metadata, session/task tables, and staged phenotype tables.

## Five measurements

| Order | Task | Field | Direction | Interpretation boundary |
|---:|---|---|---|---|
| 1 | Letter N-back | `cnb_lnb_mcr` | positive | True-positive count; denominator/load unresolved; not normalized accuracy |
| 2 | Penn Face Memory | `cnb_cpf_cr` | positive | Correct-response field |
| 3 | Penn Matrix Reasoning | `cnb_pmat_cr` | positive | Correct-response field |
| 4 | Emotion Recognition / ER40 | `cnb_er40_cr` | positive | Correct-response field |
| 5 | Short Computerized Finger Tapping | `cnb_ctap_dom` | positive | Dominant-hand mean; exact unit/aggregation remains a caveat |

These are five task measurements, not five validated cognitive domains.

## Architecture and analytical flow

```text
Pinned ds007116 checkout + verified staged phenotype payloads
  -> dataset/QC/score audits (Steps 1–3A)
  -> source observation and pair tables (Step 3B)
  -> task-level longitudinal agreement (Steps 4A/4B + reviews)
  -> synchronized five-task cohort and estimand specification (Step 5A)
  -> transformation evidence and intended decision freeze (5A-D/R/R2/F)
  -> [CURRENT BLOCKER] rebuild and independently validate task coordinates
  -> profile level/scatter/shape analysis
  -> mechanical-instability analysis
  -> ADEMP known-truth simulations
  -> Report/Caution/Refuse calibration and baseline evaluation
  -> offline auditable Evidence Engine
```

## Development history summary

| Phase | Status | What actually happened |
|---|---|---|
| Step 1 | COMPLETED / VERIFIED with initial limitation | Audited dataset identity, sessions, n-back materialization, file states, metadata, and missing annex payloads. |
| Step 1B | COMPLETED / VERIFIED | Retrieved 41 phenotype payloads into staging; verified all against Git-annex size/SHA-256 keys. |
| Steps 2, 2B, 2C, 3A | COMPLETED / VERIFIED with recorded caveats | Iteratively defined score candidates, exact QC handling, occasion mapping, exclusions, measurement evidence, and executable specifications; corrected the erroneous treatment of `Not Valid`. |
| Step 3B | COMPLETED / VERIFIED upstream | Produced task/outcome long tables, paired task/profile manifests, candidate prediction table, cohort reconciliation, SAP draft, and provenance. No model or profile result was estimated. |
| Step 4A + review | COMPLETED / VERIFIED | Face Memory longitudinal agreement for 59 pairs, bootstrap results, figures, source-based independent review. |
| Step 4B + review | COMPLETED / VERIFIED | Extended task-level agreement to all five tasks; 286 task pairs matched independent review. |
| Step 5A | COMPLETED / VERIFIED as specification | Reconstructed synchronized complete occasions and the 52-person two-occasion candidate cohort; specified profile estimands, uncertainty, missingness, and sensitivity policies. |
| Step 5A-D/R/R2 | COMPLETED / VERIFIED only as evidence support | Evaluated reference cohorts, age models, MAD vs SD, extrapolation policies, LNB semantics, and bootstrap feasibility. R2 is the last reusable pre-transformation evidence package. |
| Step 5A-F | COMPLETED as approval record | Frozen YAML/JSON records 18 approved intended decisions. It is not proof that downstream code implemented them correctly. |
| Step 5B-A/R2/R3 | IMPLEMENTED / NOT FULLY VALIDATED; QUARANTINED | Transformation tables and validators were generated, but a forensic audit found reference-fold, M1-contract, denominator, wide-table, extrapolation, and validation-independence defects. |
| Recovery Phase 1 | COMPLETED / VERIFIED as forensic audit | Identified eight issues, established the trusted boundary, and required non-destructive regeneration. |
| Rebuild | PLANNED / NOT IMPLEMENTED | No `step5ba_rebuild` directory or accepted transformed data exists. |
| Profile analysis onward | PLANNED / NOT IMPLEMENTED | No authoritative profile ICCs, simulations, thresholds, baseline comparison, or Evidence Engine exists. |

## Verified task-level findings

| Task | Pairs | ICC(A,1) | Bootstrap 95% CI | Mean later − earlier | Change 95% CI |
|---|---:|---:|---|---:|---|
| Letter N-back | 55 | 0.660377 | [0.279099, 0.854655] | 0.000000 | [-0.636364, 0.618182] |
| Face Memory | 59 | 0.560473 | [0.343745, 0.718958] | 0.847458 | [-0.372881, 2.034322] |
| Matrix Reasoning | 57 | 0.747309 | [0.564967, 0.850316] | 0.228070 | [-0.526316, 1.017982] |
| Emotion Recognition | 58 | 0.272176 | [0.123102, 0.527584] | 1.844828 | [0.896552, 2.965517] |
| Dominant Finger Tapping | 57 | 0.463781 | [0.315853, 0.583780] | 4.795322 | [2.841959, 6.836257] |

Each task used 5,000 participant-pair bootstrap resamples with seed `20260914`. These are descriptive agreement results, not proof of causality, practice effects, static traits, or individual reportability.

## Current transformation decisions: intent versus implementation

The approved intent is recorded in `chavi_analysis_ds007116_step5af_contract_freeze_20260916/`:

- primary V/F cohort: 52 participants, two complete synchronized occasions;
- V-only sensitivity: 45 participants;
- Reference A: earliest complete occasion from 109 participants (545 task rows);
- five participant-grouped folds, seed 42;
- M0 no-age coordinate primary; M1 linear-age sensitivity; M2 excluded;
- MAD scale primary and SD sensitivity;
- no primary imputation; retain extremes with leave-one-out influence diagnostics;
- M1 extrapolation policy P3: mark unsupported and use M0;
- refit transformation within bootstrap when feasible;
- level/elevation primary; scatter and shape secondary; profile correlation descriptive.

The existing transformation branch does not prove this intent was correctly implemented. Expected Reference-A held-out fold sizes are 22/22/22/22/21 and training sizes 87/87/87/87/88. Existing artifacts instead include 98/99-person and 41/42-person training evidence. The latter is consistent with fitting the wrong 52-person cohort. M1 residual scale/support semantics are also missing from the frozen contract and were added later without a clean amendment.

## Current state

The exact scientific stage is **after pre-transformation measurement/decision work, before an accepted transformation implementation**. The next legitimate milestone is a new, dated, source-based Step 5B-A rebuild. Old Step 5B directories are retained for forensic comparison only.

## Important constraints

- Never overwrite earlier milestone directories or edit `ds007116/`.
- Use Step 3B source observations and explicit manifests as inputs; never use quarantined transformed tables as source data.
- Preserve participant/session/task/stratum keys and all exclusion reasons.
- Keep Primary, V-only, and combined stratified outputs explicit and separate.
- A passing test is insufficient if it reads production parameters/outputs or shares production helpers.
- Do not begin profile inference, simulations, threshold calibration, prediction, or UI work until the rebuilt transformation passes independent validation.
- The project root has no version-control history. Historical ordering is inferred from dated directories, provenance, reports, and artifact lineage; exact prompt-by-prompt authorship is **UNKNOWN**.
- Several scripts hard-code this workspace path; relocation requires careful path refactoring.
- No dependency lockfile or requirements file exists.

## Environment verification on 1 October 2026

- `python` resolves to Python 3.14.
- All `.py` sources compile syntactically with the standard-library compiler, except inaccessible `.pytest_cache` directories which are irrelevant binaries/cache.
- Forty-three upstream `unittest` tests were freshly rerun and passed: Step 4A production 11, Step 4A review 4, Step 4B production 10, Step 4B review 8, and Step 5A 10.
- Full later-stage test execution is **BLOCKED** in the current shell: `pytest`, NumPy, pandas, SciPy, scikit-learn, statsmodels, and matplotlib are not installed in the active Python.
- Historical artifacts report successful suites, including 48/48 at Step 5A-D-R, 74/74 at R2, and 5/5 wrappers at R3. These are historical claims, not a fresh 2026-10-01 rerun; the recovery audit also invalidates R3's claimed independence.
