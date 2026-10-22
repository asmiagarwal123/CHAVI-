# CHAVI Step 5B-A Clean Rebuild and Independent Validation

**Date:** 1 October 2026  
**Folder:** `chavi_analysis_ds007116_step5ba_clean_rebuild_20261001/`  
**Result:** clean transformation rebuild validated under the researcher-adopted protocol.

## Authorization and methodology

The authorization source is **Researcher protocol adoption through the user-submitted execution prompt.** It adopts Design B, the seeded 52-target fold map, all 57 Reference-A auxiliaries, V/F Reference A for all strata, arithmetic-mean centering, normal-consistent MAD primary, sample SD sensitivity, M0 primary, and linear-age M1 sensitivity. This is not represented as historical, supervisor, or institutional approval.

The implemented outputs are internal sample-referenced task coordinates. No profile estimand, ICC, SEM/MDC, individual classification, bootstrap interval, simulation, prediction, or UI artifact was produced.

## Source, cohorts, and folds

Canonical Step 3B source and staged score/QC records were independently checked. Dataset tag 1.0.6 and commit `fc7dc36fa2598b0b2e4579baef37d148cc085207` were clean. Cohorts: Reference A 109/109/545; Primary 52/104/520; reselected strict-V 45/90/450; fixed Primary-pair strict-V 41/82/410. Both strict-V sets are Primary subsets.

Design-B held-out target counts are 11/11/10/10/10 and training counts are 98/98/99/99/99. Every fit retains all 57 auxiliaries and excludes every held-out target identity. One target fold applies to both visits and all strata. The frozen contract SHA-256 is `619aa1e05fedfc688484691cb1e54d363c8e8ff4a63b9a5e179d05d516ac23c6`.

## Parameters and output denominators

All 100 parameter records are present (5 folds × 5 tasks × 2 models × 2 scales); all are numerically supported. Outputs contain 1,380 source-stratum rows, 5,520 expanded long rows, and 1,104 wide rows. By stratum: Primary 2,080/416; reselected strict-V 1,800/360; fixed-pair strict-V 1,640/328. The unique physical-source union is 540 task records. Expanded/stratified rows are analytical records, not additional observations.

`transformed_profiles_wide.csv` contains only five task coordinates plus support/reason/provenance fields; it contains no profile-level, scatter, shape, correlation, or other profile estimand.

## Unsupported M1 observations

M0 has zero unsupported rows. All 280 unsupported expanded rows are M1 observations outside the inclusive fold-specific training-age support; corresponding M0 fallbacks remain separately labelled. Counts below are per scale method (MAD and SD have identical counts):

| Stratum | Task | Denominator per scale | Supported | Unsupported |
|---|---|---:|---:|---:|
| primary_vf | letter_nback | 104 | 94 | 10 |
| primary_vf | face_memory | 104 | 94 | 10 |
| primary_vf | matrix_reasoning | 104 | 94 | 10 |
| primary_vf | emotion_recognition | 104 | 94 | 10 |
| primary_vf | dominant_finger_tapping | 104 | 94 | 10 |
| vonly_reselected | letter_nback | 90 | 80 | 10 |
| vonly_reselected | face_memory | 90 | 80 | 10 |
| vonly_reselected | matrix_reasoning | 90 | 80 | 10 |
| vonly_reselected | emotion_recognition | 90 | 80 | 10 |
| vonly_reselected | dominant_finger_tapping | 90 | 80 | 10 |
| fixed_primary_pair_strict_v | letter_nback | 82 | 74 | 8 |
| fixed_primary_pair_strict_v | face_memory | 82 | 74 | 8 |
| fixed_primary_pair_strict_v | matrix_reasoning | 82 | 74 | 8 |
| fixed_primary_pair_strict_v | emotion_recognition | 82 | 74 | 8 |
| fixed_primary_pair_strict_v | dominant_finger_tapping | 82 | 74 | 8 |

Thus each task has 10 unsupported observations per scale in Primary, 10 per scale in reselected strict-V, and 8 per scale in fixed-pair strict-V. No unsupported value was set to zero or replaced in the M1 coordinate field.

## Independent validation

The independent validator persisted its expectations before reading production outputs. All 100 parameter and 5520 coordinate comparisons passed with zero exact/nullness failures. Maximum absolute discrepancies were `2.1316282072803006e-14` for parameters and `2.8421709430404007e-14` for coordinates, within `1e-12 + 1e-10*abs(expected)`. It checked 1720 repeated physical-source groups across strata with zero disagreement.

The executable schema verified unique keys, exact counts, five task coordinate columns, support/null semantics, and 5,520 long→wide→long task-record associations.

## Tests, determinism, and preservation

The suite ran 27 deterministic formula, boundary, output-invariant, and deliberate-corruption tests; all passed. The fresh-process repeat produced identical hashes for all 29 declared deterministic scientific artifacts. The scoped preservation inventory contains 596 historical/source artifacts with zero changes.

## Scientific limitations

These coordinates are not population norms, clinical z-scores, validated domain measures, or permanent strengths/weaknesses. Complete-case selection, anonymized/repository-session timing, LNB denominator/load uncertainty, CTAP unit/aggregation uncertainty, and task-version/administration comparability remain. Historical R2 diagnostics used Design C and are not Design-B validation. M0/MAD are adopted choices, not newly proven optimal. Bootstrap is deferred and does not block this mechanical transformation result.

## Acceptance

All source, cohort, Design-B identity, parameter/output count, unsupported-value, schema/round-trip, independent comparison, test, fresh-process, preservation, inventory, and package gates passed. This establishes computational correctness under the adopted protocol only. A separate review is required before profile analysis.
