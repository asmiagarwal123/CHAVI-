# CHAVI Step 4B reproduction and focused tests

Run from the project root:

```powershell
python .\chavi_analysis_ds007116_step4b_five_tasks_20260916\run_step4b_task_analysis.py
python -m unittest -v .\chavi_analysis_ds007116_step4b_five_tasks_20260916\test_step4b_task_analysis.py
```

The analysis uses Python `3.14.0` standard-library parsing, statistics, deterministic bootstrap resampling, and custom SVG/PNG rendering. The participant pair is the bootstrap unit; each task uses 5000 resamples with seed 20260914. Face Memory independent regression reproduction: **PASS**.

Focused checks implemented:

- known ICC(A,1) and ICC(C,1) fixture
- deterministic participant-level bootstrap
- pre-filter missing earlier/later accounting
- exact V/F QC inclusion and explicit invalidity precedence
- one primary pair per participant and strict visit ordering
- positive nominal interval enforcement and nonpositive interval rejection
- duplicate analytical-key rejection
- Face Memory independent regression reproduction
- PNG/SVG plot generation with labels, sample size, identity/zero/LoA lines
- dataset input and prior-output hashes unchanged

No dataset, Step 3A/3B directory, Step 4A directory, or Step 4A-R directory is written by the analysis script. Integrity hashes are recorded in `step4b_provenance.json`.
