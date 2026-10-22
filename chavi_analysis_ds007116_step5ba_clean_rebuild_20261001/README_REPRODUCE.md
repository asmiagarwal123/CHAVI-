# Reproduce the Clean Step 5B-A Rebuild

All project outputs are written only in `chavi_analysis_ds007116_step5ba_clean_rebuild_20261001/`. The orchestration command verifies inputs, freezes the adopted contract before fitting, reconstructs sources, runs production and independent calculations, validates schemas and round trips, runs fixtures/corruptions, repeats scientific calculations in fresh processes, checks historical preservation, writes reports, and creates the ZIP.

```powershell
& 'C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe' .\chavi_analysis_ds007116_step5ba_clean_rebuild_20261001\orchestrate_rebuild.py
```

To recreate the isolated environment without changing the project interpreter:

```powershell
python -m venv C:\tmp\chavi_step5ba_clean_env
& 'C:\tmp\chavi_step5ba_clean_env\Scripts\python.exe' -m pip install --disable-pip-version-check --no-input -r .\chavi_analysis_ds007116_step5ba_clean_rebuild_20261001\environment_requirements.txt
& 'C:\tmp\chavi_step5ba_clean_env\Scripts\python.exe' .\chavi_analysis_ds007116_step5ba_clean_rebuild_20261001\orchestrate_rebuild.py
```

The rebuild requires the CHAVI workspace sources at the relative locations recorded in `input_artifact_manifest.csv`. It does not import or modify quarantined transformation code. Bootstrap and profile analysis remain deferred.
