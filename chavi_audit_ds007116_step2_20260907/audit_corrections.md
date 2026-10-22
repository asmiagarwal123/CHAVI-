# CHAVI Step 2 audit corrections

Confirmed and repaired in `audit_v3.py`:

- IDs are explicitly classified and excluded from scientific score coverage.
- QC rows are unique by source table/QC variable/code and frequencies are direct raw-value counts.
- Outcome coverage is score-specific and distinguishes non-missing scores from table rows.
- Categorical undocumented-code checks require an applicable Levels schema; numeric fields report observed ranges and documentation gaps.
- Cognitive-only repeat counts are separate from row/session availability.
- Score direction distinguishes absent local definitions from script extraction; supported accuracy/speed interpretations are labelled as proposed where needed.
- `n/a` is not inferred to mean structural non-applicability.
- ADT `cnb_adt_cnt_200` metadata conflict is preserved and flagged.

No raw data, pointer, or pinned checkout content was changed. `audit_v2.py` and all Step 1/Step 1B outputs remain preserved.
