# Reproduction and focused tests

```powershell
python .\chavi_audit_ds007116_step2b_20260907\audit_v4.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step2b_20260907 --fixture-only
python .\chavi_audit_ds007116_step2b_20260907\audit_v4.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step2b_20260907
```

Inputs are the pinned checkout and the already verified Step 1B staging directory. No download or imaging retrieval occurs. Fixture status: `passed`.

Focused regression coverage: different tasks filling a domain across visits; discounting cannot change the five-domain intersection; missing/partial/no-QC and unresolved QC states; single visits are not repeated; continuation is flagged; outcome-matched denominators remain score-specific.
