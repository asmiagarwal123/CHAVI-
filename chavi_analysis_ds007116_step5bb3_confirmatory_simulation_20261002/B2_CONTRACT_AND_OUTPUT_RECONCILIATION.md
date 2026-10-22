# B2 contract and output reconciliation

B2 declared 499 replicates and required at least 20 valid estimates in each 2.5% nominal tail. Even with 499 valid draws, `floor(0.025*499)=12`, so the eligibility gate is impossible. The implementation applied a total-valid rule and therefore its issued intervals are exploratory, not validated under the declared rule. Historical B2 files are not rewritten.

Independent key-based reconciliation:

- `point_rows`: `14400`
- `point_unique_keys`: `14400`
- `interval_rows`: `28800`
- `interval_unique_keys`: `28800`
- `truth_rows`: `36`
- `truth_unique_keys`: `36`
- `performance_rows`: `144`
- `paired_rows`: `108`
- `interval_families`: `['basic', 'percentile']`
- `performance_interval_families`: `['']`
- `b2_zip_sha256`: `48cf1f0cb3188704abde19680f4e688f1c5cb7ae0c663ebd87403112281df12e`

The ZIP excludes `runtime_checkpoint` arrays, so point/interval row counts and published statuses can be reconciled from the ZIP; individual bootstrap values and complete failure-reason arrays cannot be audited from the ZIP alone. The B2 README references `independent_validate.py`, which is absent from the ZIP; B3 reproduction instructions point to the actual B3 validator. B2 protected_inputs_before.csv contains 80 rows, whereas its two-row after ledger is not a full preservation check. B3 repeats the same accessible path inventory before and after. Dataset-hash comparisons in B2 do not independently validate all fitted statistics or intervals.
