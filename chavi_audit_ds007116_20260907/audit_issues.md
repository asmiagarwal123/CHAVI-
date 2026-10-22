# CHAVI audit issues and retrieval blockers

## Blocking for full Paper 1 data audit

1. **Phenotype payloads unavailable:** 41 `phenotype/*.tsv` files are visible annex stubs; their target objects are absent from the local `.git/annex/objects` store. Retrieve the annex content using a snapshot-pinned DataLad/Git-annex/OpenNeuro method that keeps the repository at commit `fc7dc36fa2598b0b2e4579baef37d148cc085207` / tag `1.0.6`, then rerun this script.
2. **Full repeat coverage unknown:** without phenotype rows, cannot calculate task-specific participant/session coverage, pairwise cross-task overlap, or whether a session-level n-back observation is aligned with all other cognitive tasks.
3. **Validity semantics unresolved in observed data:** dictionaries document validity-code levels, but no phenotype validity values are locally observable. Do not filter based on the documented levels alone.

## Important non-blocking ambiguities

- Session acquisition times are rounded/anonymized; precise elapsed-time analyses require a documented transformation rule.
- `participants.tsv` age is baseline; session-table age is per-session. Use exact source variable names.
- Recruitment groups and `dx_*` indicators are different concepts; neither is a cognitive-domain label.
- Medication was not identified in `README`, `CHANGES`, `dataset_description.json`, `participants.json`, `phenotype/*.json`, or `sourcedata/` inspected material.
- No final cognitive composites, global scores, profile-shape scores, reliability coefficients, or predictive models were calculated.

## Reproducibility note

The original dataset repository was not modified. The audit output is outside the dataset repository. Hashes in `file_manifest.csv` are hashes of visible relevant metadata/tabular files; for annex stubs, they hash the visible stub text, not the absent payload. Imaging and derivative files are listed but intentionally not hashed or loaded.
