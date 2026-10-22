# CHAVI Step 1B audit report: Penn LEAD ds007116

Audit timestamp (UTC): `2026-09-07T07:50:32.287095+00:00` to `2026-09-07T07:50:54.890678+00:00`  
Dataset root: `C:\Users\asmi\Desktop\Projects\ML Projects\ds007116`  
Step 1B script: `audit_v2.py`  
Scope: retrieve and verify phenotype payloads, then audit their observed contents. No final scoring, reliability analysis, predictive modelling, clinical conclusion, dashboard, or interface was performed.

## Executive result

The checkout remains a clean `main` checkout at commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`, tag/description `1.0.6`, with the official OpenNeuroDatasets remote. The intended snapshot identity is preserved for the Git checkout. All **41/41** expected phenotype TSV payloads were retrieved into separate staging and **41/41** matched their pinned annex size/hash keys; **41** parsed successfully. No tracked pointer file or dataset branch was changed.

The verified phenotype payloads support a complete table-level audit of **21 cognitive-task tables** and **20 questionnaire/outcome tables**. Counts below are observed from payloads and use no QC-based exclusions.

## 1. Retrieval, verification, and provenance

- **Observed:** expected keys were read from the pinned checkout's `phenotype/*.tsv` pointer targets. Each key encoded a SHA-256E payload size/hash.
- **Observed:** direct S3 staging was limited to `s3://openneuro.org/ds007116/phenotype/`; all payloads matched expected size and SHA-256. The detailed per-file record is `retrieval_manifest.csv`.
- **Observed:** Git remains at `fc7dc36fa2598b0b2e4579baef37d148cc085207`, branch `main`, tag `1.0.6`, status `## main...origin/main`. The old Step 1 output directory was preserved.
- **Documented:** local `dataset_description.json` identifies DOI `doi:10.18112/openneuro.ds007116.v1.0.6`, BIDS `1.8.0`, dataset type `raw`, and license `CC0`. Local `CHANGES` identifies the 1.0.6 release date and phenotype JSON fixes in 1.0.5.
- **Externally verified:** the official GitHub 1.0.6 release maps to commit `fc7dc36`; official OpenNeuro documentation describes snapshots as Git tags and annex retrieval through DataLad/git-annex or the OpenNeuro storage remote.
- **Unresolved:** exact original download method/date is not recorded. The S3 URL alone was not treated as snapshot identity; the pinned Git-annex key match was required.

## 2. Participant, visit, and assessment counts

Counting rules: a recorded visit is one available row in `sub-*/sub-*_sessions.tsv`; a phenotype observation is one row in a verified phenotype TSV; a unique participant-session is the exact key `(participant_id, session_id)`; a non-missing score is a value not in the generic missing-token set; a repeated observation means the same participant has observed values at two or more session labels for that table/variable. No validity or comparability filter was applied.

- **Observed:** `participants.tsv` contains **132 rows** and **132 unique participants**.
- **Observed:** recorded session rows: **225**; participants with 1 / 2 / 3+ recorded visits: **59 / 53 / 20**.
- **Observed:** phenotype cognitive participant-session keys: **219**; phenotype cognitive participants: **131**; participants with repeated phenotype cognitive occasions: **70**.
- **Observed:** scanner auxiliary n-back summary rows: **201**; scanner n-back event files: **201**; scanner event rows: **38592**. These are separate from phenotype `short_letter_2back.tsv`.
- **Observed:** duplicate keys and exact duplicate rows are reported per table in `task_visit_coverage.csv` and per variable in `score_repeat_coverage.csv`; duplicate event rows are not interpreted as duplicate assessments.

## 3. Cognitive task contents and repeat coverage

`task_visit_coverage.csv` reports actual rows, columns, participants, participant-session keys, duplicates, score-bearing rows, QC-bearing rows, and available visit pairs for every phenotype table. `score_repeat_coverage.csv` reports observed scores and participants with at least two observed scores for every variable. `variable_inventory.csv` records exact source paths, column names, definitions, units, levels, observed data types, missingness, visit availability, and unresolved interpretation issues.

Repeated participants by cognitive table: `{"Age Differentiation Test": 70, "Children's Penn Word Memory Test": 70, "Children's Verbal Reasoning Test": 70, "Delayed Discounting Task": 70, "Digit Symbol Test": 70, "Effort Discounting Task": 70, "Measured Emotion Differentiation Test": 70, "Motor Praxis Test": 70, "Penn Abstraction, Inhibition and Working Memory Task": 70, "Penn Conditional Exclusion Task for Children": 70, "Penn Emotion Recognition Task for Children": 70, "Penn Face Memory Test": 70, "Penn Matrix Reasoning Test": 70, "Risk Discounting Task": 70, "Short Computerized Finger-Tapping Task": 70, "Short Letter N-Back (2 back)": 70, "Short Penn Continuous Performance Test": 70, "Short Visual Object Learning Test": 70, "Trailmaking A": 70, "Trailmaking B": 70, "Variable Short Penn Line Orientation Test": 70}`.

No single “usable sample size” is reported. Recorded visits, phenotype cognitive occasions, observed scores, assessments with QC status, and potentially comparable repeated measurements remain distinct. The last category is not finalized because task validity and administration comparability have not been specified.

## 4. Candidate domain mappings and profile coverage

`candidate_domain_mapping.csv` contains provisional mappings only. The official Penn CNB Explore Tests page supports the broad task/domain candidates used here, including n-back/working memory, digit-symbol/processing speed, memory tests/episodic memory, reasoning/spatial tests/complex cognition, emotion and age differentiation/social cognition, discounting/reward decision-making, and motor tasks/sensorimotor speed. The local tables do not establish validated CHAVI composites.

`cross_task_coverage.csv` contains exact pairwise participant-session intersections and the all-task intersection across the **21** verified phenotype cognitive tables. These counts are unfiltered coverage intersections, not profile-eligible or scientifically usable sample sizes. No global cognition, level, scatter, or shape score was calculated.

## 5. QC, missingness, and data-quality findings

- **Observed:** detailed variable-level missingness is in `missingness_summary.csv`. The report separates missing tokens, documented unknown categories, structural not-applicability, documented invalid-assessment codes, and undocumented codes.
- **Observed:** detailed code frequencies and meanings are in `qc_code_inventory.csv`. Documented valid/QC codes are retained alongside unknown/undocumented observed codes. No observation was removed.
- **Observed:** duplicate participant-session keys and exact duplicate rows are reported separately. The repeated-key counts are not automatically treated as errors until task-specific review.
- **Documented:** the README describes cognitive omissions, self-report protocol changes, and the special continuation/repeat situation for `sub-20812`; these notes are retained as documentation and not silently used as filters.
- **Unresolved:** whether `n/a` has the same substantive meaning across every questionnaire; whether a validity code applies to an entire task or selected variables; and whether rounded/anonymized acquisition times are suitable for exact follow-up intervals.

## 6. Demographic, clinical, and contextual variables

The available `participants.tsv/json` documents recruitment group, sex, race, ethnicity, baseline age, and timepoint-1 clinical-interview indicators. Recruitment group is not an individual diagnosis. Medication was not identified in the inspected dataset documentation, participant dictionary, phenotype dictionaries, or source-data material.

Session-level `age` is documented separately in session sidecars as age at the session, while participant-level `age`/`age_months` are baseline intake fields. The audit does not substitute one for the other.

## 7. Candidate outcomes and longitudinal availability

All questionnaire tables are now available and audited at inventory/coverage level. `outcome_coverage.csv` reports exact fields, rows, baseline `ses-1` coverage, non-baseline follow-up coverage, repeated participants, overlap with repeated cognitive participants, and unresolved score-direction/timing issues.

Priority outcomes requested for review:

- `eswan_adhd`: `{"baseline_ses1_rows": 132, "candidate_outcome": "E-SWAN ADHD", "exact_score_fields": "eswan_adhd_01;eswan_adhd_02;eswan_adhd_03;eswan_adhd_04;eswan_adhd_05;eswan_adhd_06;eswan_adhd_07;eswan_adhd_08;eswan_adhd_09;eswan_adhd_10;eswan_adhd_11;eswan_adhd_12;eswan_adhd_13;eswan_adhd_14;eswan_adhd_15;eswan_adhd_16;eswan_adhd_17;eswan_adhd_18;eswan_adhd_inattention_total;eswan_adhd_hyperactivity_impulsivity_total;eswan_adhd_total_score", "followup_non_ses1_rows": 91, "notes": "No outcome associations or feature selection performed.", "overlap_with_repeated_cognitive_participants": 70, "participants_with_2plus_observed_rows": 73, "priority": "high", "rows": 223, "score_direction": "not documented in inspected dictionary; do not assume", "source_path": "C:\\Users\\asmi\\Desktop\\Projects\\ML Projects\\chavi_step1b_phenotype_staging_20260907\\eswan_adhd.tsv", "stem": "eswan_adhd", "table_status": "available and parseable", "timing_ambiguity": "session_id is available; exact cognitive-assessment timing and comparability require review", "unique_participant_sessions": 223, "unique_participants": 132}`
- `mapssr`: `{"baseline_ses1_rows": 132, "candidate_outcome": "Motivation and Pleasure Scale Self-Report (MAPS-SR)", "exact_score_fields": "mapssr_1;mapssr_2;mapssr_3;mapssr_4;mapssr_5;mapssr_6;mapssr_7;mapssr_8;mapssr_9;mapssr_10;mapssr_11;mapssr_12;mapssr_13;mapssr_14;mapssr_15;mapssr_social_total;mapssr_recvoc_total;mapssr_motrelation_total;mapssr_engage_total;mapssr_total_score", "followup_non_ses1_rows": 91, "notes": "No outcome associations or feature selection performed.", "overlap_with_repeated_cognitive_participants": 70, "participants_with_2plus_observed_rows": 73, "priority": "high", "rows": 223, "score_direction": "not documented in inspected dictionary; do not assume", "source_path": "C:\\Users\\asmi\\Desktop\\Projects\\ML Projects\\chavi_step1b_phenotype_staging_20260907\\mapssr.tsv", "stem": "mapssr", "table_status": "available and parseable", "timing_ambiguity": "session_id is available; exact cognitive-assessment timing and comparability require review", "unique_participant_sessions": 223, "unique_participants": 132}`
- `wolf_im_em`: `{"baseline_ses1_rows": 132, "candidate_outcome": "Wolf Intrinsic/Extrinsic Motivation Scale", "exact_score_fields": "wolf_im_em_1;wolf_im_em_2;wolf_im_em_3;wolf_im_em_4;wolf_im_em_5;wolf_im_em_6;wolf_im_em_7;wolf_im_em_8;wolf_im_em_9;wolf_im_em_10;wolf_im_em_11;wolf_im_em_12;wolf_im_em_13;wolf_im_em_14;im_average;em_average;avg_of_im_em_averages;difference_of_im_em_averages", "followup_non_ses1_rows": 91, "notes": "No outcome associations or feature selection performed.", "overlap_with_repeated_cognitive_participants": 70, "participants_with_2plus_observed_rows": 73, "priority": "high", "rows": 223, "score_direction": "not documented in inspected dictionary; do not assume", "source_path": "C:\\Users\\asmi\\Desktop\\Projects\\ML Projects\\chavi_step1b_phenotype_staging_20260907\\wolf_im_em.tsv", "stem": "wolf_im_em", "table_status": "available and parseable", "timing_ambiguity": "session_id is available; exact cognitive-assessment timing and comparability require review", "unique_participant_sessions": 223, "unique_participants": 132}`

These are candidate later outcomes/context variables, not cognitive ground truth. No associations, prediction, or outcome-driven feature selection was performed.

## 8. Audit-script repairs

`audit_v2.py` supersedes but does not overwrite Step 1 `audit.py`. Repairs include actual staged/pointer state checks; conditional payload parsing; factual table counts; separate scanner auxiliary versus phenotype n-back handling; per-variable missingness and score-repeat coverage; observed/documented/unknown QC categories; consolidated variable dictionary; cognitive versus questionnaire classification; pairwise/all-task overlap; generated report text; and synthetic tests for unavailable pointers, resolved payloads, missing values, duplicate keys, and unknown QC codes.

## 9. Remaining blockers and recommended next decision

There is no retrieval blocker for the 41 phenotype payloads. Scientific blockers remain: task-specific validity rules, precise interpretation of score directions, comparability of repeated occasions, and a preregistered rule for candidate domain membership/profile construction. The next decision is to review and approve those definitions before any scoring or reliability analysis.

## 10. Outputs and reproduction

This Step 1B directory contains the requested retrieval manifest, payload verification report, repaired script, factual audit report, provenance JSON, file/variable/task/score/QC/missingness/cross-task/domain/outcome CSVs, and issue log. The previous Step 1 directory remains unchanged.

Rerun the synthetic tests:

```powershell
python .\chavi_audit_ds007116_step1b_20260907\audit_v2.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step1b_20260907 --fixture-only
```

Rerun the real audit:

```powershell
python .\chavi_audit_ds007116_step1b_20260907\audit_v2.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step1b_20260907
```

Software versions and counting rules are recorded in `dataset_provenance.json`; per-file expected/retrieved/verified/parseable evidence is in `retrieval_manifest.csv`.

Official sources consulted: [OpenNeuro CLI/download documentation](https://docs.openneuro.org/packages/openneuro-cli.html), [OpenNeuro Git access and snapshots](https://docs.openneuro.org/git.html), [OpenNeuro API examples](https://docs.openneuro.org/api.html), [official 1.0.6 release](https://github.com/OpenNeuroDatasets/ds007116/releases/tag/1.0.6), [official 1.0.6 README](https://raw.githubusercontent.com/OpenNeuroDatasets/ds007116/1.0.6/README), and [Penn CNB task mappings](https://webcnp.med.upenn.edu/explore-tests.html).
