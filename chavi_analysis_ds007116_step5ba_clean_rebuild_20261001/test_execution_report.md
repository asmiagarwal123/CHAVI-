# Test Execution Report

- Mechanism: Python 3.14 standard-library `unittest`.
- Command: `python -m unittest discover -s chavi_analysis_ds007116_step5ba_clean_rebuild_20261001 -p test_clean_rebuild.py -v`.
- Exit code: 0.
- Tests: 27 passed, 0 failed, 0 errors.
- Coverage: hand-checkable M0/M1 formulas; constant/zero-MAD/small-scale/near-linear/large-offset/unit-conversion fixtures; missing and boundary ages; auxiliary retention; same parameters across visits; scale/fallback semantics; long/wide keys; and deliberate corruptions for identities, Design C mislabelling, leakage, dropped auxiliaries, task/QC/source mismatch, mixed strata, pivot multiplication, M1 replacement, scale substitution, and hash changes.

The previous correction milestone's 24 tests were not treated as coordinate validation.
