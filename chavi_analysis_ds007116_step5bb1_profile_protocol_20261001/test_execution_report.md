# Test execution report

Execution date: 2026-10-01

- Independent synthetic validator: PASS, 24/24 checks.
- Unit suite: PASS, 9/9 tests.
- Required corruption paths exercised: duplicate keys; unsupported M1 coordinate contamination; held-out target copies retained in fitting; decoupled target fitting/analysis multiplicities; fold-specific auxiliary redraws; independently sampled participant visits; unmatched task/matrix metadata.
- Numerical comparison tolerance: `abs <= 1e-12 + 1e-10 * abs(expected)`.
- Large-offset validation initially exposed cancellation in direct `H.T @ z`; the production and independent algorithms were repaired to project the centered vector (`H.T @ q`), which is mathematically identical and numerically more stable. All checks then passed.
- Only deterministic synthetic fixtures were evaluated. No empirical profile statistic, bootstrap, or Monte Carlo study was executed.
