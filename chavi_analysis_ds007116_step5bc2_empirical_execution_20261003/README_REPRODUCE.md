# Reproduce CHAVI Step 5B-C2

From the project root with Python 3.14.0 and NumPy 2.5.2:

```powershell
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\code\test_c2.py
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\independent_synthetic_validator.py
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\code\run_empirical.py
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\code\independent_validate.py
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\code\reproduction_checks.py
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\code\finalize_deliverables.py
```

`c2_execution_specification.json` freezes hashes, identity orders, folds, occasion pairs, streams, tolerances and schemas. Checkpoints are cumulative, atomically created versioned files; resume selects the greatest completed compatible checkpoint only after exact provenance validation. Scientific tables exclude timestamps/runtime. Participant-linked records remain under `results/participant_linked_audit`; aggregate summaries are under `results/public_aggregate`. No external upload occurs.
