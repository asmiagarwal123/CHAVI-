# CHAVI Step 4A method notes

## Boundary

Step 4A uses only the pinned local `ds007116` metadata, the hash-verified Step 1B Face Memory payload, the Step 3A specification, the Step 3B occasion mapping and preparation artifacts, and the strict Step 3B decision register. Earlier directories and the upstream dataset were not overwritten.

The executed script is `C:\Users\asmi\Desktop\Projects\CHAVI\chavi_analysis_ds007116_step4a_face_memory_20260914\step4a_face_memory.py` with SHA-256 `daa3ff02e97dee2b3fdb21cef846d45dd050daa8bb0e6ec173e4da7fa62fe399`. The source payload hash is recorded in `step4a_provenance.json` and must equal the Git-annex expected SHA-256E content hash.

## Score

The exact source is `phenotype/penn_face_memory_test.tsv`, field `cnb_cpf_cr`. The local dictionary calls it `CPF Total Correct Responses`. Local units, an explicit score range, and an explicit higher/lower direction are not provided. The official Penn CNB page identifies Face Memory as the Penn Face Memory Test in the episodic-memory section and describes 20 target faces mixed with 20 foils. This supports the narrow task context but does not validate a CHAVI broad-domain composite.

## Eligibility and pairing

The primary QC policy includes exact local codes `V` and `F` only. Score parsing is strict and accepts only finite real numbers. `NaN`, positive infinity, negative infinity, blank/missing values, and nonnumeric values are not eligible. One pair is formed from the first two eligible observations in numeric `ses-<integer>` order. The unit of analysis is the participant pair; later eligible observations remain in the candidate accounting but do not create additional primary pairs.

The source contains 131 candidate participants, 59 included primary pairs, and 72 excluded participants. The exclusion table is mutually exclusive and partitions the candidate participant set.

## ICC convention

The primary estimate is the two-way random-effects absolute-agreement single-measure ICC(A,1), calculated from the participant-by-occasion two-column table. With `n` participants and `k=2` occasions:

`ICC(A,1) = (MS_R - MS_E) / (MS_R + (k-1)MS_E + k(MS_C-MS_E)/n)`.

`MS_R` is the participant-row mean square, `MS_C` is the occasion-column mean square, and `MS_E` is the residual mean square. Negative values are retained. A zero or nonfinite denominator is reported as undefined. Sensitivities are ICC(C,1), Pearson correlation, and Spearman correlation. Correlations describe association/ranking and are not absolute-agreement measures.

## Bootstrap

The participant pair is resampled as one unit with replacement for 5000 replicates using seed `20260914`. Duplicate sampled participants receive unique bootstrap-copy identifiers inside each resample so the repeated sampled rows are not collapsed. The CSV stores each replicate's estimates and status. Intervals are percentile intervals; failure/undefined reasons are retained rather than silently replaced.

## Timing and comparability

Session labels provide the nominal ordering. Rounded/anonymized acquisition timestamps are used only to report a nominal interval when parseable and positive. They are not exact cognitive-assessment dates. The Step 3B metadata state that task-version equivalence, administration conditions, exact cognitive timing, and scan-to-cognition alignment are unresolved; this status is carried into every included pair.

## Confirmed Step 3B boundary repairs

- Step 4A first parsed the decision register with strict CSV quoting and exact schema validation. The existing Step 3B register failed because the final field on lines 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26 lacks a closing quote. Step 4A applied only that narrow, recorded in-memory repair; the original file and its hash were preserved and the repaired content was then parsed strictly.
- Non-finite numeric values are rejected.
- Session chronology is validated explicitly; timestamp ambiguity is surfaced rather than treated as a known positive interval.
- Counts are not called reconciled without an actual benchmark; this Step 4A package uses explicit `matched`, `mismatched`, or `not_benchmarked` statuses where applicable.
- The executed script's actual path and hash are recorded.
- Step 4A includes independent synthetic tests for finite/non-finite values, duplicate keys, QC states, malformed CSV, chronology, continuation handling, known ICC values, constant scores, and bootstrap duplicate copies.

## No analysis beyond Step 4A

No standardization, age adjustment, imputation, composite, prediction, questionnaire modelling, SEM/MDC, diagnosis, profile-selection model, reporting gate, or imaging analysis is performed.
