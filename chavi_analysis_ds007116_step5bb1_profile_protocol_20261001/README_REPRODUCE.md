# Reproduce Step 5B-B1

Folder: `chavi_analysis_ds007116_step5bb1_profile_protocol_20261001/`

Status: RECOMMENDED SCIENTIFIC PROTOCOL — NOT YET ADOPTED FOR EMPIRICAL EXECUTION.

From the CHAVI workspace root:

```powershell
python .\chavi_analysis_ds007116_step5bb1_profile_protocol_20261001\prepare_profile_protocol.py
python .\chavi_analysis_ds007116_step5bb1_profile_protocol_20261001\independent_profile_validator.py
python -m unittest discover -s .\chavi_analysis_ds007116_step5bb1_profile_protocol_20261001 -p 'test_profile_protocol.py' -v
python .\chavi_analysis_ds007116_step5bb1_profile_protocol_20261001\finalize_protocol.py
```

These commands perform only integrity/support auditing and deterministic synthetic validation. There is intentionally no empirical profile-analysis command. `finalize_protocol.py` verifies preservation, two fresh-process synthetic runs, the manifest convention, and creates the ZIP. The manifest lists every package member except itself and the enclosing ZIP, avoiding circular self-hashes.
