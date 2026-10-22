# Reproduction instructions and test results

Run from `C:\Users\asmi\Desktop\Projects\ML Projects`:

```powershell
python .\chavi_audit_ds007116_step2_20260907\audit_v3.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step2_20260907 --fixture-only
python .\chavi_audit_ds007116_step2_20260907\audit_v3.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step2_20260907
```

Inputs are the pinned dataset checkout and the already verified Step 1B staging directory. The script does not download data and does not inventory imaging files. It reads only verified phenotype payloads, session sidecars, and participant metadata required for the occasion/coverage audit.

Test result: `passed`. Python: `3.14.0 (tags/v3.14.0:ebf955d, Oct  7 2025, 10:15:03) [MSC v.1944 64 bit (AMD64)]`. Git: `git version 2.53.0.windows.1`. The Step 1B staging batch remains unchanged.
