# Step 5B-B3 confirmatory simulation report

## Final verdict

**CORRECTED PILOT AND CONFIRMATORY SIMULATION COMPLETE — EMPIRICAL ANALYSIS REQUIRES SEPARATE REVIEW**

B2's 499-replicate interval gate was impossible (`floor(0.025*499)=12 < 20`), so B2 interval coverage is exploratory. The corrected replay uses 999 attempted draws, requires at least 950 valid draws, requires `floor(0.025*n_valid)>=20`, and separately persists every gate.

Corrected pilot: six scenarios, 100 outer datasets per scenario, 999 bootstrap attempts, four procedures, two scales, three endpoints, and both interval families. Confirmatory run: S1 and S5, 2,000 outer datasets each, with the same corrected contract and disjoint streams. S2/S3/S4/S6 remain diagnostic corrected-pilot scenarios.

The primary questions and compact denominators are in `confirmatory_primary_questions.csv`. Paired comparisons are computed from outer-level differences with method-specific applicable N and SD/sqrt(N) MCSEs; marginal coverage subtraction is not used. Unavailable intervals reduce available-and-covered probability over all attempted datasets but are excluded from conditional coverage.

No result establishes clinical reliability, individual reportability, developmental validity, population norms, or empirical CHAVI inference.
