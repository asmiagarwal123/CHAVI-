# CHAVI Step 3B reproduction and focused tests

Run from the project root:

```powershell
python .\chavi_audit_ds007116_step3b_20260909\prepare_step3b.py --fixture-only
python .\chavi_audit_ds007116_step3b_20260909\prepare_step3b.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --step3a-dir .\chavi_audit_ds007116_step3a_20260907 --output .\chavi_audit_ds007116_step3b_20260909
```

The script reads the pinned dataset metadata, the Step 3A executable specification and only the already verified Step 1B phenotype staging payloads. It does not download data, retrieve imaging, modify the upstream checkout, or overwrite prior audit directories.

The production run performs these focused checks:

1. Step 3A exact-QC/pairing fixture suite passes.
2. No duplicate participant/session/task/score analytical keys.
3. Editing a configured policy changes a synthetic eligibility result.
4. Participant identity is retained in every pair key.
5. The five exact task/field identities are unchanged across profile occasions.
6. The `sub-20812/ses-2` continuation cannot become a new CNB occasion.
7. Fixed-profile and candidate-cohort counts reconcile.
8. The dataset commit and git status are identical before and after the run.

Expected production summary:

```text
verified_payloads_reused: 41
task_observation_rows: 1095
paired_task_rows: 2384
profile_manifest_rows: 433
outcome_observation_rows: 1115
candidate_rows: 3300
duplicate_analytical_keys: 0
dataset_commit: fc7dc36fa2598b0b2e4579baef37d148cc085207
dataset_status: ## main...origin/main
```

`provenance_step3b.json` records SHA-256 hashes for the input payloads, selected dictionaries, participant/session metadata, executable specification and generated outputs (excluding the provenance file itself to avoid self-hash recursion). The analysis tables preserve one-based source data-row references such as `phenotype/penn_face_memory_test.tsv#data-row-1`.

No output from this package is a statistical estimate. Do not run an ICC, SEM/MDC, age model, composite, prediction model or reporting gate until the proposed choices are scientifically approved and the subsequent analysis stage is explicitly started.
