# Step 4A-R independent validation and scientific review

## VERIFIED

- All **132** registered participants are reconciled exactly once: 59 included, 72 excluded after having Face Memory observations, and 1 (`sub-23582`; see accounting) with no Face Memory source row. This proves Step 4A's 131-person candidate denominator was the set of distinct participants represented in the 219-row Face Memory payload, rather than the full registered cohort.
- Independent raw-payload selection reproduced 59 pairs and all Step 4A agreement estimates/CIs within 2e-12 after displayed-value rounding; the machine-readable comparison is `statistical_crosscheck.csv`. The independently reproduced median change is 1.0; descriptive LoA are -8.4590 and 10.1539 (mean +/- 1.96 SD), matching the original plotting formula.
- Both ICC paths agree on the synthetic fixture within 1e-10. Bootstrap uses 5,000 participant-pair resamples with seed 20260914, preserves duplicate draws, has explicit status counts, and reruns identically.
- Every included participant has exactly one numeric-session ordered pair. All observed included rounded-timestamp intervals are positive; they remain approximate anonymized acquisition intervals.

## CORRECTED

- The complete denominator is now stated as 132 registered participants. Step 4A's 131 is valid only as its task-source candidate denominator; it did not itself reconcile the one registered person absent from the task payload.
- Reviewed figures use transparent deterministic display jitter only; underlying data are unchanged. Limits of agreement are explicitly descriptive.

## UNRESOLVED

- Task version/administration equivalence and exact cognitive-assessment timing are not established by available metadata. The malformed Step 3B decision register is not used to select this review; provenance records Step 4A's documented strict failure and narrow in-memory repair, without source modification.

## CANNOT BE CLAIMED

This result cannot be called pure short-interval test–retest reliability, an individual confidence interval, clinical threshold, diagnostic result, developmental effect, practice effect, or causal attrition analysis.

## Scientific recommendation

Step 4A is sufficiently verified as a narrowly scoped, reproducible longitudinal-agreement analysis to proceed to a **separate** Step 4B analysis of the four predefined remaining tasks, provided that each task receives the same full-denominator reconciliation, raw-payload selection audit, interval caveats, and independent statistical cross-check. This review does not perform Step 4B.
