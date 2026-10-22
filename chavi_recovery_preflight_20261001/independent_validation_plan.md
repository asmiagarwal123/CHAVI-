# Independent Validation Plan for the Subsequent Step 5B-A Rebuild

## Purpose and independence boundary

The validator must reconstruct expected records, cohorts, folds, parameters, support flags, and coordinates from the pinned Step 3B source observations, the Step 3A occasion map, dataset dictionaries, and the finally approved rebuild contract. It must not import the production transformation module, copy production calculation helpers, read production parameter tables as calculation inputs, or seed its expectations from transformed outputs.

Production outputs may be opened only after the validator has persisted its independently calculated expectations and their hashes. Comparison code must be a separate final phase.

## Validator inputs

1. `chavi_audit_ds007116_step3b_20260909/task_observations_long.csv`, expected SHA-256 `8b435d4b23d0b5f70b3c56ade4215d215028426dbdb46eaaf8daaa3cd0dc1978`.
2. `chavi_audit_ds007116_step3b_20260909/assessment_occasion_mapping_step3a.csv`.
3. The five pinned phenotype dictionaries for exact field and QC meanings.
4. The approved post-preflight contract and its SHA-256.
5. The approved participant fold identity manifest and hashes.

Step 5A manifests are comparison targets only. Quarantined Step 5B-A/R2/R3 parameter and transformed tables are prohibited as validator inputs.

## Separate implementation requirement

Use an independently authored module and tests. Production and validation modules may share only language/runtime libraries and immutable input schemas. They must not share functions for cohort selection, fold assignment, mean/MAD/SD, OLS, support checking, pivoting, or hashing of analytical identities.

At review, perform a static import and similarity audit. Any import of a production package, reading of production parameter CSV before expectation calculation, or copied substantive formula helper is a validation failure.

## Reconstruction stages

### 1. Source selection

- Verify dataset tag/commit/clean state and every declared input hash.
- Assert one Step 3B source row per participant/session/task key.
- Independently confirm exact table stem, score field, QC field, finite numeric value, and raw QC meaning.
- Exclude continuation records using the occasion map, not a transformed-table flag.
- Reconstruct V/F and V-only complete synchronized occasions.
- Emit discrepancies rather than forcing 176/109/52/45.

### 2. Cohorts and identities

- Reference A: earliest complete V/F occasion for every eligible participant.
- Primary: first two complete V/F occasions.
- V-only: first two complete V-only occasions.
- Recompute the 50/52/53 identity reconciliation.
- Compare identities and source keys with production only after independent manifests are written.

### 3. Folds

- Implement the explicitly approved post-preflight algorithm verbatim.
- Verify each of 109 participants occurs in exactly one held-out fold.
- Verify held-out/training identity hashes, counts 22/22/22/22/21 and 87/87/87/87/88, and empty held-out/training intersections.
- Verify both analysis occasions of each participant select the same reference fold.
- Fail if a 545-row reference manifest coexists with parameter training identities other than the approved 87/88 sets.

### 4. Parameters and coordinates

For each task/fold/model/scale combination, independently calculate:

- M0 arithmetic mean;
- normal-consistent MAD using the exact approved constant;
- sample SD with the exact approved degrees of freedom;
- M1 OLS intercept and slope from explicit normal equations or a different library pathway than production;
- training residuals and residual scales;
- inclusive fold-specific age bounds;
- M0 and M1 coordinates and P3 fallback metadata.

Persist training participant IDs, source-row keys, hashes, and all parameters before reading production outputs.

## Numerical tolerances

Use exact equality for identities, strings, counts, raw values, QC codes, booleans, hashes, and support classifications. Suggested floating tolerances, subject to the final runtime declaration:

- mean, median, MAD, SD, OLS intercept/slope, prediction, residual: absolute tolerance `1e-12`, relative tolerance `1e-10`;
- transformed coordinates: absolute tolerance `1e-10`, relative tolerance `1e-9`;
- values intentionally rounded for display must never be calculation inputs.

Any tolerance failure must identify participant/session/task/fold/model/scale and both values. Do not round until reporting.

## Required invariants

- Reference A: 109 participants, 109 occasions, 545 unique task rows.
- Primary: 52 participants, 104 occasions, 520 unique task rows.
- V-only: 45 participants, 90 occasions, 450 unique task rows.
- Long unique key: participant, stratum, session, task, model, scale.
- Wide unique key: participant, stratum, session, model, scale.
- Every wide row has exactly five nonmissing M0 task coordinates; M1 may be missing only with an explicit reason/support flag.
- M0 has no age-extrapolation state.
- M1 support includes exact boundaries and excludes only missing age or strict outside values.
- P3 leaves `m1_coordinate` missing and stores M0 under an explicitly M0-labelled fallback field.
- Combined 970 source-row stratified view is never deduplicated across strata and never called one canonical cohort.
- Deterministic reruns reproduce identity, parameter, and output hashes.

## Edge-case tests

Use synthetic fixtures independent of production helpers:

1. constant task score: scale refusal;
2. very small but nonzero scale: approved near-zero behavior;
3. missing session age: M0 valid, M1 unsupported;
4. age exactly at minimum/maximum: supported;
5. age just outside each boundary: unsupported with M0 fallback;
6. duplicated participant bootstrap draw: retained with unique draw ID and same original fold;
7. held-out identity duplicated in bootstrap: all copies excluded from its training fold;
8. degenerate M1 age variation: invalid replicate with explicit reason;
9. nonconstant metadata during wide conversion: fail instead of multiplying rows;
10. same physical source observation in Primary and V-only: allowed only because analytical stratum differs.

## Historical-failure detection matrix

| Historical failure | Required detecting check |
|---|---|
| Correct-looking 545-row manifest but incorrect training identities | Hash actual training identity list for every parameter row; require approved 87/88 list, not only `n_reference=109` |
| 52-person fit labelled Reference A | Require every parameter training identity to be a member of the 109-person manifest and require exact fold training hashes |
| Mixed analytical strata | Include `analytical_stratum` in all keys and verify stratum-specific counts before any concatenation |
| Wide duplication from nonconstant metadata | Assert one metadata value per intended pivot key; abort on violation |
| Incorrect extrapolation denominators | Report counts separately by participant, occasion, task row, stratum, model, and scale |
| M0 inheriting M1 flags | Schema/type test requires M0 support field `not_applicable` and extrapolation `false` |
| Unspecified M1 behavior | Validator refuses to run unless every required M1 contract field is present and approved |
| Shared erroneous calculation pathway | Static import/similarity audit plus independent formulas and persisted expectations before comparison |

## Failure criteria

Any source/hash mismatch, unexpected identity/count discrepancy, duplicate analytical key, fold leakage, training-hash mismatch, undefined unhandled parameter, tolerance breach, nondeterministic rerun, report/CSV denominator mismatch, or independence violation fails the rebuild. A failed gate blocks profile analysis; it must not be downgraded to a warning merely because aggregate results look plausible.

