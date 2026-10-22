# CHAVI Implementation History

**Reconstructed from repository evidence on:** 1 October 2026  
**History limitation:** the project root is not a Git repository. Only `ds007116/` has Git metadata, so project-file history is reconstructed from dated stage directories, provenance files, reports, hashes, source code, outputs, and the recovery audit. Exact prompt-by-prompt changes and deleted/overwritten untracked versions are **UNKNOWN / REQUIRES CONFIRMATION**.

## Status key

This document uses: **COMPLETED / VERIFIED**, **IMPLEMENTED / NOT FULLY VALIDATED**, **IN PROGRESS**, **PLANNED / NOT IMPLEMENTED**, and **UNKNOWN / REQUIRES CONFIRMATION**.

## Phase-by-phase reconstruction

### 1. Initial dataset audit — 6–7 September 2026

**Status: COMPLETED / VERIFIED with a then-current payload limitation**

`chavi_audit_ds007116_20260907/` introduced `audit.py` and 11 report/data artifacts. It verified the OpenNeuro repository identity and inventoried 24,575 files, 132 participants, 225 sessions, materialized n-back summaries/events, metadata, missingness, and candidate task/domain mappings. At that time, the phenotype TSVs were annex pointers without local payloads, so full-battery analysis was explicitly blocked.

### 2. Phenotype retrieval and Step 1B audit

**Status: COMPLETED / VERIFIED**

`chavi_step1b_phenotype_staging_20260907/` contains 41 staged TSV payloads. `chavi_audit_ds007116_step1b_20260907/` added `audit_v2.py`, retrieval/hash manifests, a consolidated dictionary, cross-task coverage, repeat coverage, QC inventory, and verification reports. Evidence records 41/41 payloads matching pinned annex size/hash keys and 41 parseable tables. The raw dataset pointers were not modified.

### 3. Score, QC, and occasion feasibility — Steps 2, 2B, 2C, 3A

**Status: COMPLETED / VERIFIED with documented caveats**

The implementation evolved through `audit_v3.py` to `audit_v6.py` in four non-destructive stage directories. Outputs include variable/score manifests, QC rules in CSV/YAML, assessment-occasion maps, pair manifests, feasibility tables, evidence registers, decision registers, exclusion flows, executable JSON specifications, SAP drafts, and focused fixtures.

Important change: an earlier QC approach could include text containing `Valid` even when the exact state was `Not Valid`. Later stages corrected this by using exact dictionary meanings and precedence rules. Valid, likely-valid, invalid, skipped, excluded, unresolved, missing, partial, and absent states remain distinct.

`chavi_audit_ds007116_step3a_20260907/` also contains copied predecessor artifacts plus targeted corrections and implementation closure. These directories are historical milestones, not one clean package with a single reusable library.

### 4. Analysis-data preparation — Step 3B, 9 September 2026

**Status: COMPLETED / VERIFIED upstream**

`prepare_step3b.py` generated:

- `task_observations_long.csv` — 1,095 source task-observation rows;
- `paired_task_observations.csv` — 2,384 rows;
- `paired_profile_manifest.csv` — 433 rows;
- `candidate_prediction_cohort.csv` — 3,300 rows;
- `outcome_observations_long.csv` — 1,115 rows;
- occasion mapping, reconciliation, data dictionary, decision register, SAP, provenance, input and retrieval manifests.

No standardized coordinate, imputation, ICC, age model, prediction model, profile result, or Evidence Engine decision was produced in this phase.

### 5. Face Memory agreement — Step 4A and independent review, 14 September 2026

**Status: COMPLETED / VERIFIED**

`step4a_face_memory.py` created the 59-pair included manifest, 72 exclusions, descriptive/agreement/5,000-bootstrap result tables, and PNG/SVG plots. It applied a narrowly documented in-memory repair to a malformed quoted Step 3B CSV register without changing the source file.

`validate_step4a.py` independently selected pairs from the raw staged payload and reproduced the estimates. The review reports agreement within numerical tolerance, deterministic bootstrap reproduction, and ICC formula validation. The main verified result is ICC(A,1) `0.560473`, 95% CI `[0.343745, 0.718958]`.

### 6. Five-task agreement — Step 4B and review, 16 September 2026

**Status: COMPLETED / VERIFIED**

`run_step4b_task_analysis.py` extended the same design to five tasks. It generated 286 paired observations, 25,000 bootstrap rows, task-specific agreement/descriptive tables, exclusions, interval audit, and 20 plots. `validate_step4b.py` produced an independent 286-row pair manifest, 80 statistical crosschecks, 25 bootstrap checks, formula/plot/integrity reviews, and reviewed Bland–Altman images.

The original Step 4B PNG annotations omitted exact score-field tokens; Step 5A records this as a presentation-only correction with no numerical change. SVG metadata and plotted calculations were accepted.

### 7. Synchronized profile specification — Step 5A

**Status: COMPLETED / VERIFIED as a measurement specification**

`prepare_step5a_measurement_specification.py` reconstructed 176 complete synchronized V/F occasions, 109 participants with at least one, and 52 with two. The 52-person pair source trace contains 520 task rows. It reconciled the apparent 50/52/53 discrepancy and produced cohort, age, score-semantics, formula, missingness, uncertainty, sensitivity, and mechanical-instability planning artifacts.

This phase specified but did not compute authoritative profile coordinates or reliability estimates.

### 8. Transformation decision evidence — Step 5A-D, R, and R2

**Status: COMPLETED / VERIFIED only as pre-transformation evidence**

Step 5A-D created a draft contract and diagnostics but remained `not_ready`. Step 5A-D-R corrected nine deficiencies, including LNB interpretation, V/F QC wording, deterministic fold assignment, reference-only age fitting, residual/extrapolation diagnostics, MAD comparison, bootstrap feasibility, and the four-dimensional constraint on five centered components.

R1 used a 52-person reference in important diagnostics. R2 then compared the intended 109-person Reference A against the 52-person Reference B, ran M0/M1/M2 comparisons, MAD/SD diagnostics, extrapolation policies, and 1,000 bootstrap-feasibility replicates. R2 recommended Reference A, M0 primary, M1 sensitivity, MAD primary, SD sensitivity, P3 extrapolation behavior, and refit-within-bootstrap. Its report records 74/74 historical tests.

### 9. Supervisor decision freeze — Step 5A-F

**Status: COMPLETED as an approval record; not implementation proof**

`SUPERVISOR_APPROVAL.yaml` records approval of decisions D1–D18. `step5af_transformation_contract_frozen.json` is version `0.3.0`, status `frozen`, and records the approved values and a hash of the approval YAML.

Known contract gap: it names M1 as retained sensitivity in narrative/approval but the JSON sensitivity list does not fully specify M1 residual scale and support semantics. That omission becomes critical downstream.

### 10. Transformation attempts — Step 5B-A, R2, and R3

**Status: IMPLEMENTED / NOT FULLY VALIDATED; QUARANTINED**

The first Step 5B-A branch generated a 545-row reference manifest, 25 parameter rows, 540 long rows, a malformed/mixed 120-row wide table, support flags, traces, claims, and a short validation report. R2 expanded/combined strata into 970 long rows and 206 wide rows. R3 separated 520 Primary and 450 V-only task rows, added M1 coordinates/support outputs, and claimed independent validation.

These implementations are not authoritative. The later recovery audit found:

- Reference A requires 109 participants and fold training sizes 87/88, but artifacts show 98/99 or 41/42;
- 41/42 implies fitting the 52-person primary cohort, not Reference A;
- M1 semantics were added after freeze without a clean contract amendment;
- 120/206-row wide tables mix or duplicate stratum metadata;
- 540 and 970 rows use different meanings/denominators;
- extrapolation counts 55/60/70/75/140 cannot be compared without stable keys;
- validators read production parameters/outputs or share helpers, so their passing tests are self-consistency evidence, not independent validation.

No profile level, shape, scatter, ICC, simulation, threshold, or Evidence Engine result was generated in these branches.

### 11. Recovery Phase 1 forensic audit — 16 September 2026

**Status: COMPLETED / VERIFIED as current trust decision**

`recovery_phase1_audit.py` and the 25-file audit package inventoried 913 artifacts, compared contracts/parameters/tables, classified validator independence, reproduced stable upstream counts, and registered issues CHAVI-001 through CHAVI-008. It did not modify earlier artifacts.

The trusted boundary is Step 5A plus R2 evidence. Step 5A-F is approval intent only. Step 5B-A through R3 must be regenerated.

### 12. September 30 master handoff

**Status: COMPLETED / VERIFIED as a documentation correction**

`CHAVI_MASTER_PROJECT_SPECIFICATION_AND_HANDOFF.md` and `summary.md` supersede the older `chavi_antigravity_handoff_20260916/` snapshot. The older handoff says Step 5B had not started; that was correct when written but is not the final workspace history. Later Step 5B attempts exist and are quarantined.

## Testing and validation history

Historical evidence includes fixture scripts, `unittest` suites, `pytest` suites, deterministic bootstrap checks, file/hash checks, and source-based review packages. Notable recorded claims include 48/48 tests at Step 5A-D-R, 74/74 at R2, and 5/5 pytest wrappers at R3.

Current verification on 1 October 2026:

- dataset Git identity and clean state: verified;
- CSV artifact dimensions: re-inventoried;
- Python syntax compilation: passed;
- 43 upstream standard-library tests: freshly passed (11 Step 4A production, 4 Step 4A review, 10 Step 4B production, 8 Step 4B review, 10 Step 5A);
- full later-stage tests: **BLOCKED**, because the active Python lacks `pytest` and the scientific packages;
- R3 independence claim: rejected by the recovery audit regardless of historical green tests.

## Files created or modified

Because the project root has no Git history, an exact modified-file list per prompt cannot be recovered. Repository evidence establishes that each dated stage directory contains its stage's scripts, reports, outputs, manifests, and provenance. Later stages copied or patched some earlier scripts and artifacts rather than modifying a centrally versioned package. Root-level transformation/recovery scripts were also added, but their exact authorship and prompt association are **UNKNOWN**.

## Known bugs and limitations

1. CHAVI-001 through CHAVI-008 in the recovery issue register remain unresolved/confirmed as documented.
2. Early reproduction text embeds the former `ML Projects` path; later transformation scripts hard-code the current CHAVI path.
3. No project-level `.git`, dependency lockfile, or install manifest exists.
4. Some `.pytest_cache` directories are inaccessible to the sandbox; they are generated caches, not scientific inputs.
5. The LNB denominator/load mapping and exact CTAP unit/aggregation remain unresolved.
6. Long/anonymized intervals limit reliability interpretation.
7. The sample is not suitable for population or clinical norms.

## Current implementation status

The next implementation is not a patch to old tables. It is a new dated Step 5B-A rebuild with an amended, machine-readable contract and a genuinely independent source reconstruction validator. Until that passes, the project remains at the pre-transformation acceptance boundary.
