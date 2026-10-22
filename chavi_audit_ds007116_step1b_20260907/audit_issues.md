# CHAVI Step 1B audit issues

## Resolved

- All 41 expected phenotype TSV payloads were retrieved into staging and matched their pinned SHA-256E size/hash keys.
- All 41 retrieved phenotype tables parsed successfully.
- DataLad/git-annex absence was handled by the documented staged S3 fallback; no tracked pointer file was overwritten.

## Remaining scientific uncertainties

- Validity/QC codes are observed and documented in `qc_code_inventory.csv`, but no exclusion rule was applied. Unknown/undocumented codes and explicit unknown categories are retained separately.
- `n/a`, missing, structurally not-applicable, invalid-assessment, and unknown-category values are separate fields in `missingness_summary.csv`; their scientific treatment remains for review.
- Session-level age in `sub-*/sub-*_sessions.tsv` and baseline age in `participants.tsv` are different sources. Phenotype tables have participant/session keys but no universal proof that every task's assessment time exactly aligns with scan time.
- Scanner n-back summaries/events and `phenotype/short_letter_2back.tsv` are kept separate because their documentation and task context differ; they are not interchangeable measures.
- `cross_task_coverage.csv` reports exact participant-session intersections without QC filtering. It does not establish a final profile-eligible sample.
- No final domain/global/profile scores, reliability coefficients, predictive models, or reporting thresholds were calculated.

## Retrieval record

Direct S3 retrieval was limited to `s3://openneuro.org/ds007116/phenotype/`; no MRI, derivative, other dataset, or whole-dataset download was performed. The source checkout remains at `fc7dc36fa2598b0b2e4579baef37d148cc085207` with status `## main...origin/main`. See `retrieval_manifest.csv` for per-file evidence.
