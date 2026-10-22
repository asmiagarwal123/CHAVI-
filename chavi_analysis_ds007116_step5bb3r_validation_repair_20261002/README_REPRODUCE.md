# STEP 5B-B3-R reproduction

This directory is a bounded simulation implementation audit. It contains no empirical CHAVI profile inference and does not authorize one.

Environment used: Windows 11, Python 3.14.0, NumPy 2.5.2. From the project root:

```powershell
python -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install --prefer-binary --progress-bar off -r requirements.txt
Set-Location chavi_analysis_ds007116_step5bb3r_validation_repair_20261002
```

Core executable checks:

```powershell
& '..\.venv\Scripts\python.exe' reproduce_defects.py
& '..\.venv\Scripts\python.exe' independent_corruption_checks.py
& '..\.venv\Scripts\python.exe' run_edge_case_tests.py
& '..\.venv\Scripts\python.exe' impact_screen.py
& '..\.venv\Scripts\python.exe' independent_full_replicate_validate.py
& '..\.venv\Scripts\python.exe' independent_table_reconcile.py
& '..\.venv\Scripts\python.exe' truth_sensitivity.py
& '..\.venv\Scripts\python.exe' run_reproduction_tests.py
& '..\.venv\Scripts\python.exe' validate_repaired_checkpoints.py
```

Affected same-stream recalculation is resumable and atomic. Run these stage/scenario combinations; existing valid checkpoints are reused only after `validate_repaired_checkpoints.py`:

```powershell
& '..\.venv\Scripts\python.exe' recalculate_affected.py --stage corrected_pilot --scenario S1
# repeat corrected_pilot for S2..S6
& '..\.venv\Scripts\python.exe' recalculate_affected.py --stage confirmatory --scenario S1
& '..\.venv\Scripts\python.exe' recalculate_affected.py --stage confirmatory --scenario S5
& '..\.venv\Scripts\python.exe' consolidate_repaired.py
```

The exhaustive scale-support screen runs `scale_support_stream_screen.py` for the same eight stage/scenario combinations. `make_final_report.py` refuses readiness unless both stages and every listed validation gate pass.

Raw 999-value independent verification is intentionally a pre-frozen 15-record subset, not all 4,600 outers. Full-record checks cover all dataset identities, all repaired checkpoint provenance, and all exported interval/summary arithmetic. The original full B3 runtime is not duplicated in the final ZIP; exact regeneration commands and hashes are retained instead.
