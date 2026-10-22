# CHAVI Step 1 dataset audit: Penn LEAD (ds007116)

Audit timestamp (UTC): `2026-09-06T19:17:27.219312+00:00` to `2026-09-06T19:17:42.912364+00:00`  
Dataset root: `C:\Users\asmi\Desktop\Projects\ML Projects\ds007116`  
Audit script: `audit.py`  
Scope: non-destructive metadata and tabular audit only. No MRI volume was loaded, no imputation, scoring, reliability analysis, prediction, or modelling was performed.

## Executive result

The local checkout is a clean Git checkout of the official `OpenNeuroDatasets/ds007116` repository at commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`, with local tag/description `1.0.6`. The metadata and documentation identify DOI `doi:10.18112/openneuro.ds007116.v1.0.6` and CC0. This establishes the Git checkout identity, but not the availability of every payload object.

The local repository contains 132 rows in `participants.tsv`, 132 participant session tables with 225 recorded session rows, 201 materialized session-level n-back summary rows, and 201 materialized n-back event files with 38592 event rows. The full phenotype battery is not locally available: 41 phenotype TSVs are annex stubs whose target objects are absent from `.git/annex/objects`. Therefore no full-battery missingness, cross-task overlap, domain-score, profile, ICC, SEM, MDC, or outcome-overlap result is supportable from this checkout.

Interpretation labels below use: **Observed** = calculated from materialized local content; **Documented** = stated in local documentation; **Externally verified** = checked against official online documentation; **Proposed** = cautious candidate interpretation; **Unresolved** = cannot be established from available material.

## 1. What was inspected and what remained unavailable

Inspected: Git metadata, `dataset_description.json`, `README`, `CHANGES`, `participants.tsv/json`, all phenotype dictionaries, all visible `*_sessions.tsv/json` files, all visible n-back `*_events.tsv/json` files, file states/pointers, and high-level directory/file inventory. MRI volumes and derivatives were inventoried by path/size/state only; they were not loaded or hashed.

Unavailable: the underlying objects for phenotype TSVs and most large imaging/derivative files. The visible annex stubs point to `.git/annex/objects/...`, but the local annex object store contained no files at audit time. The phenotype JSON dictionaries are available, but they do not supply rows, missingness, visit coverage, or observed validity codes.

## 2. Repository and dataset provenance

- **Observed:** remote is `origin	https://github.com/OpenNeuroDatasets/ds007116.git (fetch)
origin	https://github.com/OpenNeuroDatasets/ds007116.git (push)`; branch is `main`; `git status` reported `## main...origin/main`; `git describe` is `1.0.6`; tag(s) at HEAD: `1.0.6`.
- **Observed:** local `dataset_description.json` has BIDSVersion `1.8.0`, DatasetType `raw`, DOI `doi:10.18112/openneuro.ds007116.v1.0.6`, License `CC0`, and `ReferencesAndLinks` values `TODO` / `List of papers or websites`.
- **Documented:** `CHANGES` lists 1.0.6 on 2026-07-28 and notes a sidecar-key warning fix; 1.0.5 fixed phenotype JSON typos; 1.0.3 updated events TSV files; 1.0.1 added session age and the phenotype folder.
- **Externally verified:** the official GitHub release page for 1.0.6 maps the tag to short commit `fc7dc36`; the official raw 1.0.6 metadata matches the local DOI/name/license. The official README describes the same 132-adolescent dataset and the same cognitive/self-report inventories.
- **Unresolved:** download method and download date are not recorded in the inspected local documentation. Local file timestamps are copy/check-out timestamps, not provenance evidence. No evidence of a mixed Git-version working tree was observed, but absent annex payloads prevent checking payload content beyond the pointer paths committed at HEAD.

## 3. Participant, visit, and cognitive-assessment counts

Counting rules: a recorded visit is one row in an available `sub-*/sub-*_sessions.tsv`; a unique participant-session is the `participant_id/session_id` key; an n-back summary observation requires at least one non-missing n-back summary variable in that row; an n-back event observation requires at least one materialized event table for that participant/session. These are availability counts, not “usable” counts. No validity-based exclusion rule was applied.

- **Observed:** unique participants in `participants.tsv`: **132**; participant rows: **132**; subject directories: **132**.
- **Observed:** available session files: **132**; unique participant-session keys: **225**; session rows: **225**.
- **Observed:** participants with 1 / 2 / 3+ recorded session rows: **59 / 53 / 20**. The first number is written this way to make clear it is the count at key `1`, not a total of rows.
- **Observed:** n-back summary rows: **201**, unique participants: **122**, unique participant-sessions: **201**; n-back event files: **201**, event rows: **38592**, unique event participant-sessions: **201**.
- **Observed:** duplicate participant IDs in `participants.tsv`: `none`. Duplicate participant-session keys in available session tables: `none`.
- **Observed:** IDs in subject directories but not `participants.tsv`: `none`; participant IDs without subject directories: `none`.

Recorded visit pair counts (all session rows): `{"ses-1 + ses-2": 73, "ses-1 + ses-3": 20, "ses-2 + ses-3": 20}`. N-back-summary pair counts: `{"ses-1 + ses-2": 60, "ses-1 + ses-3": 16, "ses-2 + ses-3": 19}`. Event-table pair counts: `{"ses-1 + ses-2": 60, "ses-1 + ses-3": 16, "ses-2 + ses-3": 19}`. These pair counts are descriptive and do not establish comparable measurement occasions.

No cross-task overlap for the full CNB battery can be calculated because the phenotype tables are unavailable. Ten of the 132 session files have only `session_id`, `age`, and `acq_time` in the header; this is evidence of missing n-back summary coverage in those materialized session files, not proof that all cognitive tasks were absent.

## 4. Cognitive task and variable inventory

The local `README` names 21 cognitive tasks from the Penn CNB. Their dictionaries are present under `phenotype/`, but the corresponding TSV tables are annex stubs. The materialized local cognitive data are narrower:

- `sub-*/sub-*_sessions.tsv`: session-level n-back counts, hit/false-alarm rates, and d-prime variables where the header is present. The sidecar defines `age` as fractional years at the time of each session and `acq_time` as rounded/anonymized acquisition time.
- `sub-*/ses-*/func/*_task-nback*_events.tsv`: trial/event rows with `onset`, `duration`, `trial_type`, `results`, `response_time`, and `score`. These are trial-level event data, not a general rule for all reaction-time fields in the phenotype battery.
- `phenotype/*.json`: exact variable names, task labels, units, and documented validation-code levels. The dictionary does not establish score direction, validated composites, or a common QC rule across tasks.

Exact variable-level documentation is in `variable_inventory.csv`. The script records both documentation and unresolved issues rather than inferring that higher is better or that all tasks share one validity scheme.

## 5. Candidate domain mappings

`candidate_domain_mapping.csv` contains only provisional task-to-domain candidates. The official Penn CNB Explore Tests page supports mappings such as Letter-N-Back to working memory, Digit-Symbol to processing speed, Word/Face/Visual Object tests to episodic memory, Matrix/Verbal/Line Orientation tests to complex cognition, Emotion/Age Differentiation to social cognition, discounting tasks to reward decision-making, and Motor Praxis/Finger Tapping to sensorimotor or motor speed. The local AIM task name combines multiple constructs, and Conditional Exclusion/Trailmaking are left provisional pending task-specific documentation.

No final domain scores, global scores, profile level, scatter, or shape scores were calculated.

## 6. Missingness, QC, and repeat coverage

- **Observed:** available-table missingness is in `missingness_summary.csv`. Event-level `n/a` values are treated as task-defined not-applicable values for missingness summaries; instruction rows are not silently treated as failed cognitive trials.
- **Observed:** event QC/value frequencies are in `qc_code_inventory.csv`. Unknown event codes would be listed explicitly. No phenotype validity-code frequencies can be observed because phenotype TSV payloads are unavailable; their documented levels are retained with observed count `0 (table unavailable)`.
- **Observed:** among the 201 n-back summary rows with at least one observed summary variable, 201 have all 27 n-back summary variables non-missing and 0 are partial. No row was removed. Event code counts for the materialized tables are `{"results": {"Match": 6030, "NR": 32562}, "score": {"false_negative": 1406, "false_positive": 1039, "n/a": 14472, "true_negative": 17051, "true_positive": 4624}, "trial_type": {"0BACK": 12060, "2BACK": 12060, "INSTRUCTION": 14472}}`.
- **Observed:** n-back range/ceiling checks are `[{"variable":"0_back_false_positive","n_numeric":201,"min":0.0,"max":12.0,"out_of_documented_proportion_range":0,"exact_zero":111,"exact_one":49},{"variable":"0_back_false_negative","n_numeric":201,"min":0.0,"max":15.0,"out_of_documented_proportion_range":0,"exact_zero":153,"exact_one":13},{"variable":"0_back_true_positive","n_numeric":201,"min":0.0,"max":15.0,"out_of_documented_proportion_range":0,"exact_zero":10,"exact_one":1},{"variable":"0_back_true_negative","n_numeric":201,"min":33.0,"max":45.0,"out_of_documented_proportion_range":0,"exact_zero":0,"exact_one":0},{"variable":"2_back_false_positive","n_numeric":201,"min":0.0,"max":42.0,"out_of_documented_proportion_range":0,"exact_zero":22,"exact_one":20},{"variable":"2_back_false_negative","n_numeric":201,"min":0.0,"max":15.0,"out_of_documented_proportion_range":0,"exact_zero":8,"exact_one":24},{"variable":"2_back_true_positive","n_numeric":201,"min":0.0,"max":15.0,"out_of_documented_proportion_range":0,"exact_zero":12,"exact_one":1},{"variable":"2_back_true_negative","n_numeric":201,"min":3.0,"max":45.0,"out_of_documented_proportion_range":0,"exact_zero":0,"exact_one":0},{"variable":"all_back_true_positive","n_numeric":201,"min":0.0,"max":30.0,"out_of_documented_proportion_range":0,"exact_zero":10,"exact_one":0},{"variable":"all_back_true_negative","n_numeric":201,"min":40.0,"max":90.0,"out_of_documented_proportion_range":0,"exact_zero":0,"exact_one":0},{"variable":"all_back_false_positive","n_numeric":201,"min":0.0,"max":50.0,"out_of_documented_proportion_range":0,"exact_zero":19,"exact_one":15},{"variable":"all_back_false_negative","n_numeric":201,"min":0.0,"max":30.0,"out_of_documented_proportion_range":0,"exact_zero":7,"exact_one":22},{"variable":"0_back_all_correct","n_numeric":201,"min":38.0,"max":60.0,"out_of_documented_proportion_range":0,"exact_zero":0,"exact_one":0},{"variable":"0_back_all_incorrect","n_numeric":201,"min":0.0,"max":22.0,"out_of_documented_proportion_range":0,"exact_zero":83,"exact_one":51},{"variable":"2_back_all_correct","n_numeric":201,"min":18.0,"max":60.0,"out_of_documented_proportion_range":0,"exact_zero":0,"exact_one":0},{"variable":"2_back_all_incorrect","n_numeric":201,"min":0.0,"max":42.0,"out_of_documented_proportion_range":0,"exact_zero":1,"exact_one":3},{"variable":"all_back_all_correct","n_numeric":201,"min":70.0,"max":120.0,"out_of_documented_proportion_range":0,"exact_zero":0,"exact_one":0},{"variable":"all_back_all_incorrect","n_numeric":201,"min":0.0,"max":50.0,"out_of_documented_proportion_range":0,"exact_zero":1,"exact_one":2},{"variable":"0_back_hit_rate","n_numeric":201,"min":0.0,"max":1.0,"out_of_documented_proportion_range":0,"exact_zero":10,"exact_one":153},{"variable":"0_back_false_alarm_rate","n_numeric":201,"min":0.0,"max":0.26666666666666666,"out_of_documented_proportion_range":0,"exact_zero":111,"exact_one":0},{"variable":"2_back_hit_rate","n_numeric":201,"min":0.0,"max":1.0,"out_of_documented_proportion_range":0,"exact_zero":12,"exact_one":8},{"variable":"2_back_false_alarm_rate","n_numeric":201,"min":0.0,"max":0.9333333333333332,"out_of_documented_proportion_range":0,"exact_zero":22,"exact_one":0},{"variable":"all_back_hit_rate","n_numeric":201,"min":0.0,"max":1.0,"out_of_documented_proportion_range":0,"exact_zero":10,"exact_one":7},{"variable":"all_back_false_alarm_rate","n_numeric":201,"min":0.0,"max":0.5555555555555556,"out_of_documented_proportion_range":0,"exact_zero":19,"exact_one":0},{"variable":"0_back_dprime","n_numeric":201,"min":0.0,"max":4.120462587126895,"out_of_documented_proportion_range":0,"exact_zero":1,"exact_one":0},{"variable":"2_back_dprime","n_numeric":201,"min":-0.1495440969589009,"max":4.120462587126895,"out_of_documented_proportion_range":0,"exact_zero":0,"exact_one":0},{"variable":"all_back_dprime","n_numeric":201,"min":0.4111395794663277,"max":4.667230047836295,"out_of_documented_proportion_range":0,"exact_zero":0,"exact_one":0}]`. For proportion variables, values outside [0,1] are flagged; exact 0/1 concentrations are descriptive only and were not used to filter observations.
- **Documented:** the README records task-level cognitive omissions and self-report missingness/protocol changes, including the special continuation/repeat situation for `sub-20812`, and states that session acquisition time was rounded for anonymization. These notes are not substituted for row-level verification of unavailable tables.
- **Unresolved:** whether repeated scans, continuation sessions, and cognitive assessments are comparable; whether a missing phenotype row means no assessment, an unavailable extract, or a task-specific missing value; and how validity codes should be handled across tasks.

## 7. Demographic, clinical, and contextual variables

`participants.tsv/json` documents `study_group`, `sex`, `race`, `ethnicity`, baseline `age_months`/`age`, and timepoint-1 clinical-interview indicators `dx_none`, `dx_prodromal`, `dx_prodromal_remit`, `dx_psychosis`, `dx_moodnos`, `dx_mdd`, `dx_bp`, `dx_adhd`, `dx_ptsd`, and `dx_ptsd_remit`. `study_group` is a recruitment/experimental group with levels ADHD, TD/NC, and PRO/CHR; it must not be treated as an individual diagnosis. Baseline age is not the same as session age.

Medication search: inspected `README`, `CHANGES`, `dataset_description.json`, `participants.json`, `phenotype/*.json`, and `sourcedata/` for medication/stimulant terms. Matching files: `phenotype/age_differentiation_test.json, phenotype/delay_discounting_task.json, phenotype/digit_symbol.json, phenotype/effort_discounting_task.json, phenotype/measured_emotion_differentiation_test.json, phenotype/motor_praxis.json, phenotype/penn_abstraction_inhibition_working_memory_task.json, phenotype/penn_conditional_exclusion_task.json, phenotype/penn_emotion_recognition_task.json, phenotype/penn_face_memory_test.json, phenotype/penn_matrix_reasoning_test.json, phenotype/penn_verbal_reasoning_test.json, phenotype/penn_word_memory_test.json, phenotype/risk_discounting_task.json, phenotype/short_computerized_finger_tapping_task.json, phenotype/short_letter_2back.json, phenotype/short_penn_continuous_performance_test.json, phenotype/substance.json, phenotype/trailmaking_test_a.json, phenotype/trailmaking_test_b.json, phenotype/variable_short_penn_line_orientation_test.json, phenotype/visual_object_learning_test.json`. Medication was **not identified in the inspected material**.

## 8. Candidate outcomes and longitudinal availability

The README names self-report scales including ALES, ALS-18, ARI, ASRM, BDI-1A, BIS-BAS, E-SWAN ADHD/DMDD, MAPS-SR, PANAS, PPA, PRIME, RPAS, RSAS, Substance Use, Tanner scales, Wolf IM/EM, and pre/post STAI. Their dictionaries are present, but their TSV data are unavailable locally. Consequently baseline/follow-up availability, overlap with cognitive observations, and score direction remain unresolved here. `outcome_coverage.csv` records these as candidates only; no outcomes were used for predictor selection.

## 9. Files relevant and irrelevant to CHAVI Paper 1

- **A — relevant now:** `participants.tsv/json`; `sub-*/sub-*_sessions.tsv/json`; n-back `*_events.tsv/json`; phenotype dictionaries; `dataset_description.json`, `README`, `CHANGES`; Git-annex/file-state metadata.
- **B — potentially useful later:** phenotype TSV payloads once retrieved; full self-report tables; additional task event or summary files; code/CuBIDS summaries; documented QC lists; session timing after its anonymization implications are resolved.
- **C — not required for Paper 1 at this stage:** MRI volumes, field maps, DWI/ASL/MEGRE volumes, FreeSurfer and task-contrast derivatives, unless a later preregistered validity question specifically requires them. They were inventoried at high level only.
- **D — unavailable or ambiguous:** phenotype TSV payloads and most large annexed objects; observed validity/QC codes for phenotype tasks; full cross-task overlap; medication variables; any claim that the full CNB battery is locally analyzable.

## 10. Conflicts between assumptions and observed data

1. The intended snapshot is supported for the Git checkout, but local data payload availability is incomplete because annex objects are absent.
2. The README describes a 132-participant, multi-task longitudinal dataset, but the materialized cognitive payload available for direct counting is mainly n-back session summaries/events.
3. Session-level `age` is documented as age at each session; `participants.tsv` age is documented as baseline intake age. They must not be swapped.
4. Session dates/times are rounded/anonymized; exact follow-up intervals should not be treated as precise without a documented de-identification transformation.
5. A task name or existing summary variable is not evidence of a validated CHAVI domain composite.
6. The presence of an `events.tsv` response-time column demonstrates trial-level response times for that n-back task only; it does not establish trial-level data in all phenotype RT variables.

## 11. Remaining uncertainties and scientific-review questions

- Which exact phenotype payloads should be retrieved, and how will retrieval preserve the verified 1.0.6 snapshot?
- What is the source-of-truth rule for a cognitive occasion when BIDS sessions, CNB sessions, repeat scans, and incomplete/continued visits disagree?
- Which task variables and validity codes are admissible before any reliability analysis, and are rules task-specific?
- Are session-level n-back summaries intended as candidate Paper 1 outcomes, or only as an auxiliary task with separate provenance?
- Which candidate domain mappings are scientifically justified for this specific Penn LEAD battery, and which should remain unassigned?
- What minimum repeated-occasion and cross-task overlap criteria should be preregistered before scoring?

## 12. Audit outputs and reproduction

Created in this directory: `audit_report.md`, `dataset_provenance.json`, `file_manifest.csv`, `variable_inventory.csv`, `participant_visit_summary.csv`, `task_visit_coverage.csv`, `qc_code_inventory.csv`, `missingness_summary.csv`, `candidate_domain_mapping.csv`, `outcome_coverage.csv`, `audit_issues.md`, and `audit.py`.

Rerun from the workspace parent with:

```powershell
python .\chavi_audit_ds007116_20260907\audit.py --dataset .\ds007116 --output .\chavi_audit_ds007116_20260907
```

The script records Python/Git versions in `dataset_provenance.json`. It does not download, modify, clean, reset, checkout, or update the dataset repository.

## 13. Recommended next decision before scoring or modelling

**Decide and document the exact retrieval plan for the missing phenotype TSV payloads, with snapshot-preserving provenance, before any scoring or modelling.** After retrieval, repeat this audit and require row-level checks for task/session identity, validity-code semantics, cross-task overlap, baseline versus session age, and repeated-visit comparability. Until that is done, the checkout supports metadata audit and a limited n-back availability audit, not the planned full multidomain CHAVI Paper 1 analysis.

## Official sources consulted

- [Official GitHub repository](https://github.com/OpenNeuroDatasets/ds007116)
- [Official 1.0.6 raw dataset description](https://raw.githubusercontent.com/OpenNeuroDatasets/ds007116/1.0.6/dataset_description.json)
- [Official 1.0.6 README](https://raw.githubusercontent.com/OpenNeuroDatasets/ds007116/1.0.6/README)
- [Official 1.0.6 CHANGES](https://raw.githubusercontent.com/OpenNeuroDatasets/ds007116/1.0.6/CHANGES)
- [Official 1.0.6 GitHub release](https://github.com/OpenNeuroDatasets/ds007116/releases/tag/1.0.6)
- [Penn CNB Explore Tests](https://webcnp.med.upenn.edu/explore-tests.html)
- [Penn CNB overview](https://webcnp.med.upenn.edu/about.html)
