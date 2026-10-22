# Step 5B-B2 implementation hardening and known-truth simulation pilot

## Final verdict

**SIMULATION PILOT COMPLETE — CONFIRMATORY VALIDATION REQUIRED**

This milestone is simulated-data-only. No empirical CHAVI profile inference, bootstrap, M1 analysis, strict-V analysis, prediction, reportability, BCa interval, or large factorial analysis was executed.

## Execution

- Frozen design: six scenarios × 100 outer datasets; 52 target identities and 57 auxiliaries; five fixed folds (11, 11, 10, 10, 10).
- Procedures: P1 oracle conditional, P2 estimated-reference fixed-transform, P3 identity-linked unstratified joint refit, P4 identity-linked fold-stratified joint refit.
- Scales: population/estimated MAD and sample SD. S6 MAD has an explicitly undefined population target and is never silently replaced by SD.
- Endpoints: ICC(A,1), mean level change, and RMS centered-shape displacement.
- Bootstrap: 499 replicates, percentile and basic intervals, linear quantiles, no redraw of failures.
- Completed outer datasets: 600/600.

## Reproducibility and validation

The contract freezes NumPy PCG64DXSM keyed streams, master seed 20261002, scenario registry, fold assignment, and checkpoint semantics. `truth_results.csv` records analytic or independent large-sample targets and convergence diagnostics. Mechanism checks A–I and the independent validation JSON are preserved. The fresh-process deterministic comparison covers the preselected first five datasets per scenario.

## Interpretation boundary

At 100 outer datasets, Monte Carlo error is material; performance summaries are a bounded implementation pilot, not confirmatory evidence. Any future confirmatory execution must use the recommended specification and independently resolve the upstream fold-contract decision.
