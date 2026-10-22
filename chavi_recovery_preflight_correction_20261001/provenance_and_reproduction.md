# Provenance and Reproduction

## Milestone folder

All new outputs are in `chavi_recovery_preflight_correction_20261001/`. Historical milestones were read-only.

## Environment

- Windows 11 (`Windows-11-10.0.26200-SP0`)
- Python 3.14.0 at `C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe`
- NumPy 2.5.2
- Dataset Git: clean tag 1.0.6, commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`
- Test mechanism: Python standard-library `unittest`; no pytest dependency

## Commands and outcomes

```powershell
& 'C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe' -m py_compile .\chavi_recovery_preflight_correction_20261001\reconstruct_and_audit.py .\chavi_recovery_preflight_correction_20261001\test_corrected_preflight.py
# exit 0

& 'C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe' .\chavi_recovery_preflight_correction_20261001\reconstruct_and_audit.py
# exit 0; consolidated computational gate passed

& 'C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe' -m unittest discover -s .\chavi_recovery_preflight_correction_20261001 -p 'test_corrected_preflight.py' -v
# exit 0; 24 tests passed; 34 assertion calls in source

& 'C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe' .\chavi_recovery_preflight_correction_20261001\reconstruct_and_audit.py --verify-existing
# exit 0; fresh-process scientific reconstruction matched
```

JSON parse, CSV parse, package-manifest verification, ZIP creation, and ZIP SHA-256 are performed by `finalize_package.py` after all authored files exist.

## Fresh and historical evidence

Fresh checks: raw-source cohort derivation; two eligibility-flag comparisons; 41 payload hash/size checks; dictionary meanings; staged row score/QC comparison; unique keys/mappings/frame membership; 50/52/53 identities; two strict-V definitions; A/B candidate maps; historical fold-map identity comparison; code hashes; 24 targeted tests; fresh-process repeat; and 79-artifact scoped before/after hash comparison.

Historical evidence not rerun as production analysis: R2 model comparisons and bootstrap feasibility; Step 5B-A/R2/R3 coordinates and parameters. Those outputs remain quarantined and were inspected only for implementation classification/preservation.

## Determinism and hashing

Identity hashes are SHA-256 over lexicographically sorted participant IDs joined by LF, with a final LF. Candidate contract hashing is non-self-referential: its digest appears in `milestone_artifact_manifest.csv`, not inside the contract. The manifest excludes itself while computing member hashes; the ZIP includes the finalized manifest. ZIP SHA-256 is reported outside the ZIP.

## Preservation scope

`historical_artifact_before_after_hashes.csv` covers the prior preflight's declared inputs, every file and ZIP in that prior milestone, the named implementation scripts, and selected protected parameter/coordinate artifacts. All 79 matched. No broader claim is made about unrelated workspace files or large imaging payloads.
