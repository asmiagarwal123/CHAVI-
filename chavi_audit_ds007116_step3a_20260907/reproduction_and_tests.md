# Step 3A reproduction

```powershell
python .\chavi_audit_ds007116_step3a_20260907\audit_v6.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step3a_20260907 --spec .\chavi_audit_ds007116_step3a_20260907\step3a_specification.json --fixture-only
python .\chavi_audit_ds007116_step3a_20260907\audit_v6.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step3a_20260907 --spec .\chavi_audit_ds007116_step3a_20260907\step3a_specification.json
```

Fixture status: `passed`. Production checks executed: `production_continuation_no_new_CNB, production_scheduled_observation_and_pair_reconciliation, production_outcome_numeric_and_intersection_reconciliation, production_exclusion_flow_reconciliation`. The script reuses verified Step 1B payloads and performs no download, imaging retrieval, scoring, reliability estimation, prediction, or Evidence Engine work.
