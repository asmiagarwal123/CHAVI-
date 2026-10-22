# CHAVI Step 4B review report

Step 4B is a task-level longitudinal dependability analysis of five prespecified raw Penn LEAD fields. It does not construct profiles or make diagnostic, clinical, predictive, AI, or external-dataset conclusions.

## Results

| Task | Candidate participants | Excluded | Pairs | ICC(A,1) | Bootstrap 95% CI | Mean later-minus-earlier | Bootstrap 95% CI | Bland-Altman LoA |
|---|---:|---:|---:|---:|---|---:|---|---|
| Letter N-back | 131 | 76 | 55 | 0.660377 | [0.279099, 0.854655] | 0.000000 | [-0.636364, 0.618182] | [-4.741358, 4.741358] |
| Face Memory | 131 | 72 | 59 | 0.560473 | [0.343745, 0.718958] | 0.847458 | [-0.372881, 2.034322] | [-8.458992, 10.153907] |
| Matrix Reasoning | 131 | 74 | 57 | 0.747309 | [0.564967, 0.850316] | 0.228070 | [-0.526316, 1.017982] | [-5.569896, 6.026036] |
| Emotion Recognition | 131 | 73 | 58 | 0.272176 | [0.123102, 0.527584] | 1.844828 | [0.896552, 2.965517] | [-6.087486, 9.777141] |
| Dominant Finger Tapping | 131 | 74 | 57 | 0.463781 | [0.315853, 0.583780] | 4.795322 | [2.841959, 6.836257] | [-10.353478, 19.944121] |

## Accounting and QC

For every task, candidate participants partition exactly into one included primary pair or one exclusion. Missing earlier and later score counts are reported in `five_task_descriptive_results.csv` under `pre_pair_missingness` before complete-pair filtering. Exclusions retain row-level reasons and observed QC/score statuses in `five_task_exclusions.csv`. Exact `V` and `F` are primary inclusion codes; invalid, skipped, excluded, unresolved, missing, and nonfinite states are not silently merged.

## Timing

Pairs are ordered by numeric session label and require a strictly positive nominal session interval. Rounded/anonymized acquisition timing is reported separately; missing or nonpositive timing is not silently treated as an exact positive cognitive-assessment interval. Interval distributions and timing missingness are in `five_task_interval_audit.csv`.

## Face Memory reproduction

Face Memory independent reproduction: **PASS**. The detailed comparison is in `face_memory_reproduction_check.csv`; the required independent result is n=59, ICC(A,1) approximately 0.560473, bootstrap CI approximately [0.343745, 0.718958], and mean change approximately 0.847458 with CI approximately [-0.372881, 2.034322].

## Boundaries

No arbitrary reliability labels are applied. Correlation, ICC, and mean-change estimates describe the released score fields across eligible recorded occasions only; they do not separate development, practice, state change, and measurement noise, and they do not establish task-version equivalence or clinical validity.

## Reproducibility

The pinned dataset Git state before and after execution is required to remain clean at `fc7dc36fa2598b0b2e4579baef37d148cc085207`. Step 4A and Step 4A-R inputs are hash-recorded. Prior Step 4A output directories are hash-checked before and after execution. Focused tests are listed in `step4b_reproduction_and_tests.md`.

## Scientific-review readiness

Five-task task-level foundation ready for scientific review: **YES**, conditional on review of the explicit task-specific exclusions, unresolved timing/version metadata, and interval distributions. This package does not automatically continue to Phase 2.
