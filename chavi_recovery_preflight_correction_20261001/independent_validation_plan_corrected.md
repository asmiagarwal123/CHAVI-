# Corrected Independent Validation Plan

## Independence boundary

The later validator must reconstruct cohorts, chosen fold identities, fitting identities, parameters, support, and coordinates from Step 3B, the occasion map, pinned dictionaries, staged payloads, and the approved contract. It must not import production calculation helpers or read production parameter/coordinate outputs until expected values and their hashes have been persisted.

## Required gates

1. Verify source/dictionary/input hashes and dataset tag/commit.
2. Re-derive eligibility from finite raw score and exact raw QC, not upstream eligibility flags; compare both V/F and strict-V flags afterward.
3. Reject duplicate source or occasion-map keys, missing mappings, wrong table/field combinations, unregistered identities, and staged source score/QC disagreement.
4. Reproduce Reference A 109/109/545, Primary 52/104/520, reselected strict-V 45/90/450, fixed-primary-pair strict-V 41/82/410, and 50/52/53 identities. Count equality without identity equality fails.
5. Load the explicitly approved candidate identity hashes. For recommended Design B, verify 52 seeded target folds, 57 auxiliaries always retained, fitting counts 98/98/99/99/99, and no held-out identity in any fit.
6. Independently calculate M0 mean, normal-consistent MAD, ddof=1 SD, M1 OLS/intercept/slope/residual scales, effective-age identity hashes, and inclusive support bounds.
7. Exercise exact, numerical, and small-valid scales; rank-deficient/constant-age and missing-age M1; boundary ages; missing scores; and no silent SD substitution.
8. Validate long and wide keys. Reject nonconstant metadata within a wide pivot key. Assert M0 age support is `not_applicable`; unsupported M1 is null with a separately labelled M0 fallback.
9. Reconcile source denominators before variant expansion: 520, 450, and 970 stratified rows. Never call variant rows new observations.
10. If bootstrap is later implemented, use synthetic identity fixtures first: joint multiplicities, unique draw IDs, retained auxiliaries, and exclusion of every held-out copy.

## Numerical comparison

Compare integer/string/identity/hash/support fields exactly. For independently calculated floating values, require `abs(a-b) <= 1e-12 + 1e-10*abs(expected)` unless an approved contract specifies a tighter task-specific tolerance. Compare nullness before numeric tolerance.

## Failure reporting

One consolidated gate must list failures by source key or parameter key. Keep three states separate: computational/source/schema failure; unresolved scientific decision; expected disagreement between alternative candidates. A candidate-design disagreement is not a data error, and a passing computational gate is not contract approval.

## Required targeted tests

The validator suite must retain deliberately corrupted fixtures for bad upstream V/F and V flags, duplicate source/map keys, missing mapping, correct counts/wrong identities, valid Design B, Design C mislabeled Reference A, held-out leakage, pivot metadata splits, M0 inheriting M1 support, M1 missing/constant age, duplicate bootstrap-copy leakage, and scale degeneracy. Tests must report names, counts, assertions, command, exit code, and environment.

## Acceptance boundary

Production transformation is acceptable only after human approval of the contract and identity map, an independently authored implementation, a separately authored validator, exact identity/source/schema gates, numerical comparisons within tolerance, deterministic rerun hashes, and preservation of protected historical artifacts. Passing this preflight does not validate future coordinates.
