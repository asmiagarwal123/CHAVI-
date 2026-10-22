# Step 5B-B3 reproduction

This package contains simulated-data calculations only. It does not import empirical CHAVI profiles or generate empirical ICCs, bootstrap intervals, individual reports, clinical interpretations, prediction, or UI artifacts.

Environment: `C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe`, Python 3.14.0, NumPy 2.5.2. Run `python test_simulation.py`, then `python audit_b2.py`. The corrected stage resumes with `set CHAVI_STREAM_NAMESPACE=corrected_pilot` and `python run_stage.py --stage corrected_pilot`; the confirmatory stage uses `set CHAVI_STREAM_NAMESPACE=confirmatory` and `python run_stage.py --stage confirmatory`. Checkpoint records are under `runtime/<stage>/` and are intentionally omitted from the transferable ZIP; any record can be regenerated from the contract, code, stream namespace, scenario, and outer ID.

After a stage completes, run `python consolidate.py --stage corrected_pilot` or `python consolidate.py --stage confirmatory`, then `python independent_validate.py --stage ...`. The independent validator writes expectations before comparison and checks hashes, point estimates, selected bootstrap values, and failure/eligibility records. It is a substantive second implementation and does not import `simulation_core.py` or `run_stage.py`.

The exact contract hashes, protected-file before/after inventory, manifest, ZIP membership, and SHA-256 are recorded with the milestone.
