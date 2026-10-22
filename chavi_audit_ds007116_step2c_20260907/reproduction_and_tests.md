# Step 2C reproduction

```powershell
python .\chavi_audit_ds007116_step2c_20260907\audit_v5.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step2c_20260907 --spec .\chavi_audit_ds007116_step2c_20260907\step2c_specification.json --fixture-only
python .\chavi_audit_ds007116_step2c_20260907\audit_v5.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step2c_20260907 --spec .\chavi_audit_ds007116_step2c_20260907\step2c_specification.json
```

The script reuses only the 41 verified Step 1B payloads; it does not download or retrieve imaging. Executed fixtures: `passed`.
