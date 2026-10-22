# Changes from CHAVI Step 1 to Step 1B

Step 1 record: `chavi_audit_ds007116_20260907/audit.py` and its reports.  
Step 1B successor: `audit_v2.py` in this directory.  
Dataset checkout preserved at `fc7dc36fa2598b0b2e4579baef37d148cc085207` / tag `1.0.6`.

## Retrieval

- Retrieved only the 41 expected `phenotype/*.tsv` payloads into a separate staging directory.
- Verified each staged payload against the expected SHA-256E size/hash encoded in the pinned Git-annex pointer.
- Did not overwrite tracked pointer files or modify the dataset branch.

## Audit corrections

- Replaced hard-coded unavailable phenotype narratives with conditional pointer/staging/payload state checks.
- Parsed actual phenotype rows and generated actual rows, columns, participants, participant-session keys, duplicate-key counts, exact duplicate-row counts, and visit-pair counts.
- Added score-level repeat coverage and separate missing-score counts; validity/completion fields are not counted as scientific scores.
- Added observed QC/code frequencies, documented meanings, unknown-category counts, invalid-code counts, structural-not-applicable counts, and undocumented-code counts.
- Added a consolidated dictionary with one row per table variable, preserving definition conflicts rather than duplicating identical session dictionaries.
- Classified tables as cognitive, questionnaire/outcome, demographic/context, or scanner-task auxiliary data.
- Kept scanner n-back summaries/events separate from phenotype `short_letter_2back.tsv`.
- Added exact pairwise and all-task participant-session coverage for candidate cognitive profiles.
- Added actual baseline/follow-up and repeated-cognitive overlap summaries for questionnaires, with priority rows for E-SWAN ADHD, MAPS-SR, and Wolf IM/EM.
- Added synthetic temporary tests for unavailable pointers, resolved payloads, missing values, duplicate keys, and unknown QC codes.

## Scientific boundary retained

No final cognitive composites, global scores, profile-shape scores, ICC/SEM/MDC, predictive models, thresholds, or clinical conclusions were produced.
