# Reproduce Step 5B-C1

Use the project-local environment from repository root. Only Python 3.14.0 and NumPy 2.5.2 are required; do not rely on the root `requirements.txt` implicitly.

```powershell
.\.venv\Scripts\python.exe -m pip install --requirement chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\requirements_step5bc1.txt
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\independent_synthetic_validator.py
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\analysis_interface.py --dry-run --coordinates chavi_analysis_ds007116_step5ba_clean_rebuild_20261001\primary_vf_transformed_long.csv --source chavi_analysis_ds007116_step5ba_clean_rebuild_20261001\primary_vf_source_rows.csv --model M0 --scale MAD --stratum primary_vf
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\finalize_package.py
```

The dry-run validates metadata, identities, support, and hashes only; it does not calculate endpoints. `analysis_interface.py` refuses empirical execution in this milestone. Seed construction, tolerances, gates, checkpoint keys, and resume validation are frozen in `empirical_analysis_contract.json` (SHA-256 `0bd5b1a187e33ecf70013d6b2e62f6c3b0b754b6f65bc096849e95ee50e6703a`). The validator exits nonzero on any failure. The finalizer reruns tests/dry-run, verifies protected hashes and emptiness, then rebuilds the manifest and ZIP.
