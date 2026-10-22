# Step 5A reproduction and tests

Run from the repository root:

```powershell
python chavi_analysis_ds007116_step5a_measurement_specification_20260916/prepare_step5a_measurement_specification.py
python -m unittest discover -s chavi_analysis_ds007116_step5a_measurement_specification_20260916 -p 'test_*.py' -v
```

The preparation script uses only local pinned dataset, staged payload, Step 3A/3B, Step 4B, and Step 4B-R artifacts. It reconstructs complete same-session occasions from raw verified task rows, applies exact V/F eligibility, excludes the documented continuation, chooses the first two jointly complete occasions per participant, and writes provenance hashes. It does not create standardized, centered, composite, elevation, shape, scatter, reliability, prediction, threshold, or clinical outputs.
