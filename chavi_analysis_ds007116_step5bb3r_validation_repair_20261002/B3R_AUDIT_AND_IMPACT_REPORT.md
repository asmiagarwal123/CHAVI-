# STEP 5B-B3-R — bounded validation repair and impact report

## Scope and preservation

This was an implementation audit of simulated evidence only. No empirical CHAVI participant profile was calculated. The historical B3 directory, runtime checkpoints, contracts, results, and ZIP were treated as protected inputs. The input ZIP matched the required SHA-256 `18251e4b88f67c6df2d3dd4c6e427c4de0237e2081690769852c3f9a7e0bc9ff`. B3R work was written to a separate directory.

## Defects reproduced

All four specified defects were reproduced before repair.

- The nine corruption-check PASS rows were literals, not test results. They were unsupported validation claims; this does not invalidate the genuine assertions in `mechanism_checks.py`.
- In the fold-0 fixture with weights 26, 26, then zero, B3 `batch_refit` returned three nonfinite endpoints. The scalar path retained ICC `-0.008246116815642983` but lost the two change endpoints; explicit expansion produced ICC `-0.00824611681564298`, mean change `0.7751229164598996`, and RMS `0.7600593893148766`.
- A constructed positive near-zero scale was accepted by the optimized path and rejected by the scalar 64-epsilon rule.
- Historical independent validation covered all dataset hashes, point outers 0–4, and seven bootstrap positions in outers 0–1. It did not compare any complete 999-vector, quantiles, gates, interval bounds, coverage, or full summary arithmetic. Historical readiness also ignored confirmatory independent-validation status.

## Narrow repair

Only implementation and validation mechanics changed. Zero-weight identities are removed before coordinate checks and reductions; unrepresented folds are not fit; active nonfinite coordinates remain failures; optimized support now applies the scalar finite/positive/present-count/64-epsilon rule. Frequency weights remain equivalent to explicit expansion. Linked target weights, paired visits, held-out-fold exclusion, one shared auxiliary draw, MAD constant, sample-SD convention, endpoints, frozen truths, 999 attempts, 950-valid gate, tail gate, linear quantiles, and both interval families are unchanged.

The RNG itself was preserved. Actual keys are SHA-256 of master seed, namespace, stream label, scenario, and outer. Contract prose incorrectly listed stage, method, and replicate as separate key parts. In the implementation, namespace represents stage, methods share the frozen multiplicity arrays, and replicate is row position. A new guard makes stage/namespace mismatch an error; streams were not changed to match inaccurate prose.

## Executable validation

The replacement corruption suite accepted a valid control and rejected nine mutations for the required reasons. All 9 passed. The numerical edge suite passed 12/12, including absent folds, zero-weight and active NaNs, unequal weights, odd/even medians, zero/near-zero scales, constant profiles, negative ICC, affine invariance, MAD/SD optimized-scalar equivalence, and namespace mismatch.

The frozen independent numerical audit contains 15 outer records, 68 method-scale arrays, every scenario/method/scale/endpoint, and targeted absent-fold, unsupported-fit, and exact-950-valid cases. A scalar explicit-expansion implementation importing no production fitting, endpoint, quantile, eligibility, or summary helper matched all 203,796 replicate-endpoint values/statuses. It also matched all 4,600 dataset hashes. A separate full-table path checked all 220,800 interval rows and every 384 performance and 384 paired-comparison rows with zero failures. This is full-table verification plus subset raw-value verification, not a claim that all 4.6 million raw bootstrap vectors were independently recalculated.

## Impact screen and same-stream recalculation

Exact NumPy 2.5.2 streams reproduced 111 absent-fold P3 draws in 106 confirmatory S1 outers and 112 in 110 S5 outers, matching the review diagnostic despite its NumPy 2.3.5 environment. Across both stages there were 257 unique affected draws in 248 outers. Every affected outer was regenerated for all 999 P3 draws, both scales, and all endpoints, with original datasets, multiplicities, points, truths, and namespaces. The 248 atomic checkpoints revalidated their source runtime SHA-256 and dataset hash.

The repaired scale-support rule was screened over 18,381,600 P3/P4 method-scale draws. Corrected-pilot draws were checked directly; confirmatory reference pools used a stronger lower bound valid for every possible nonnegative integer weighting. There were zero old-supported/new-rejected keys. The smallest supported-SD margin exceeded the numerical threshold by a factor of 42,967.

No interval became available or unavailable. Corrected-pilot coverage counts did not change. Confirmatory coverage changed in one secondary cell: S1/SD/P3/basic mean-level-change coverage rose from `0.9440` to `0.9445` (one outer). Primary S1/MAD RMS and S5/MAD RMS coverage/availability counts were unchanged. Widths moved only through repaired quantiles: the largest mean-width change was `6.3902e-05` in the 100-outer corrected pilot and `3.76094e-06` in confirmatory results. `original_vs_repaired_results.csv` retains every changed and zero-change comparison cell.

For the S1/MAD RMS percentile primary comparison, P2 covered **1606/2000** with **2000/2000 available** (`80.30%`); P3 covered `1835/2000` (`91.75%`) with all available. The latter is below nominal 95%, not evidence of nominal performance. For S5/MAD RMS percentile intervals, P2 availability was `1994/2000` with conditional coverage `91.8756%` and available-and-covered probability `91.60%`; P3 availability was `1260/2000` with conditional coverage `95.6349%` but available-and-covered probability only `60.25%`. Conditional coverage cannot be interpreted without availability. No interval family was selected after observing results.

## Truth and reproducibility

An isolated run of `truth_engine.py` followed by the documented exact-S5-zero correction reproduced `truth_results.csv` byte-for-byte. The missing convergence dependency was restored byte-for-byte from B2 and independently regenerated to the same hash. The frozen truth was not overwritten. S5 sensitivity at frozen truth ±4 documented numerical SE is recorded separately; the analytic mean-change zero has no numerical uncertainty.

Three genuine separate processes tested atomic checkpoints: one stopped after one checkpoint, a second resumed to completion, and a fresh calculation was byte-identical. No temporary checkpoint remained.

## Interpretation limits and remaining decisions

These simulations do not establish clinical reliability, individual reportability, general MAD-bootstrap validity, developmental validity, population norms, or methodological novelty. They do not choose an interval family and do not authorize empirical inference. The next decision, if separately authorized, is an empirical protocol review with its own estimands, missingness rules, multiplicity policy, reporting limits, and governance.

## Completion checklist

- PASS — Original defects reproduced and scope established: `defect_reproduction.json`, `defect_register.csv`.
- PASS — Executable corruption and edge tests: `independent_corruption_checks.json`, `edge_case_test_results.json`.
- PASS — Affected records identified/recalculated: `affected_replicate_inventory.csv`, `checkpoint_validation_results.json`.
- PASS — Independent full-replicate subset and full-table reconciliation: `independent_numerical_validation_results.json`, `independent_table_validation_results.json`.
- PASS — Original-versus-repaired impact: `original_vs_repaired_results.csv` and corrected stage tables.
- PASS — Truth, RNG, checkpoint, and reproduction evidence: corresponding JSON/CSV records.
- PASS — Historical preservation and package verification: before/after inventory, manifest, staged package verification, and adjacent final ZIP hash/CRC record.
- PASS — No empirical profile inference generated; limitations and next decision are stated above.
