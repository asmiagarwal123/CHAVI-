# CHAVI Corrected Preflight and Decision Review

**Date:** 1 October 2026  
**Milestone folder:** `chavi_recovery_preflight_correction_20261001/`  
**Status:** candidate specification, not approved  
**Scope:** correction and decision preparation only; no parameters, coordinates, empirical bootstrap, profile results, simulations, thresholds, predictions, or UI were produced.

## Outcome

The upstream source findings from the earlier preflight remain supported, and the new consolidated computational gate passes. The critical correction is that 98/99-person fitting sets are not intrinsically inconsistent with Reference A. They are exactly what Design B produces when the 52 analysis targets are folded, held-out targets are excluded, and all 57 auxiliary Reference-A identities remain in training.

The historical intent is nevertheless ambiguous and internally inconsistent. The approval record names the 109-person Reference A, but its fold basis reports 52 target folds and never states whether auxiliaries remain. Quarantined Step 5B-A and BAR2 code implement Design B (98/98/99/99/99). The R2 age-model diagnostic and R3 engine/validator implement Design C by dropping the 57 auxiliaries (41/41/42/42/42), even while using Reference-A language. Recovery Phase 1 instead specifies Design A identities and, separately, uses unpermuted sorted round-robin despite the frozen seeded wording.

This package recommends Design B as primary, pending human approval. It uses the approved 109-person Reference A, guarantees no analysed target contributes to its own fitted parameters, retains all auxiliary reference information, and matches the historical Step 5B-A identity mechanism. Literal seeded Design A is a defensible later sensitivity. Design C is not Reference A and requires a superseding reference decision.

## Corrected cross-fit comparison

| Candidate | Fold universe | Held out | Fitting count | Finding |
|---|---:|---:|---:|---|
| A, literal seeded | 109 reference | 22/22/22/22/21 | 87/87/87/87/88 | mathematically valid; identities differ from Recovery |
| A, Recovery sorted round-robin | 109 reference | 22/22/22/22/21 | 87/87/87/87/88 | matches Recovery identities; contradicts literal permutation wording |
| B, seeded targets + auxiliaries | 52 targets | 11/11/10/10/10 | 98/98/99/99/99 | recommended; exact historical target-fold map; no self-inclusion |
| C, target-only | 52 targets | 11/11/10/10/10 | 41/41/42/42/42 | not Reference A |

`crossfit_candidate_identity_maps.csv` carries held-out, auxiliary, and fitting lists and reproducible hashes for every candidate fold. All are explicitly candidates. The historical code inventory includes SHA-256 values and identity-based classifications rather than inferring design from counts.

For both strict-V comparisons, the recommendation is to retain the V/F Reference-A fitting reference and reuse the Primary target fold/parameters. Target eligibility and fitting-reference eligibility are separate decisions; no new V-only fitting population is silently created.

## Independent source reconstruction

Eligibility was derived from each exact task/table/score/QC field, finite numeric score, raw `V`/`F` meanings in the pinned dictionaries, and the occasion/continuation rule. Upstream eligibility flags were not membership inputs. Comparison afterward found:

- zero V/F flag mismatches;
- zero strict-V flag mismatches;
- zero duplicate source or occasion-map keys;
- zero missing selected-occasion mappings;
- zero selected field/table mismatches or unregistered identities;
- zero staged-payload participant/session/raw-score/QC mismatches across the 1,095 selected Step 3B rows;
- all 41 staged payload hashes and sizes still match the retrieval manifest.

Fresh cohort results are Reference A 109/109/545, Primary 52/104/520, and reselected strict-V 45/90/450. The complete V/F pool is 176 occasions. The five task-pair intersection is 53, aligned task pairs are 50, and jointly complete Primary is 52. Counts were comparison targets, not forced values.

All retained occasions remain only candidate-comparable by repository session label. Exact cognitive timing, administration conditions, released task-version equivalence, LNB denominator/load mapping, and CTAP unit/aggregation remain unresolved measurement limitations.

## QC and pairing correction

The first-two-V-only sensitivity changes both QC eligibility and visit selection for:

| Participant | Primary pair | Reselected strict-V pair |
|---|---|---|
| sub-20149 | ses-1; ses-2 | ses-2; ses-3 |
| sub-20310 | ses-1; ses-2 | ses-2; ses-3 |
| sub-20902 | ses-1; ses-2 | ses-2; ses-3 |
| sub-20916 | ses-1; ses-2 | ses-1; ses-3 |

It therefore cannot be called a QC-only comparison. The package defines a second, fixed-primary-pair strict-V comparison: keep the Primary visits and require all ten selected records to be raw `V`. It contains 41 participants, 82 occasions, and 410 task rows. Exact identities are in `qc_pairing_sensitivity_identity_comparison.csv`.

## Transformation and output corrections

The recommended contract makes M0 executable: apply direction first; use the fold-specific Design-B training population; arithmetic mean center; normal-consistent MAD primary; ddof=1 SD sensitivity; one fold/parameter set for both visits; no imputation; and M0 age support marked not applicable.

M1 is sensitivity-only OLS with intercept on Step3B `session_age`. It records age exclusions and effective training identity hashes, rejects constant/rank-deficient training ages, uses prediction residuals with zero residual center and training residual MAD/SD, and applies an inclusive fold-specific age interval. Missing/out-of-support M1 remains null with a reason; any M0 fallback is stored in explicitly M0-labelled fields.

The prior proposal `scale <= 1e-12*max(1,abs(center))` changes when the score origin is translated and is not unit-equivariant around the fixed `1`. It is not recommended. The candidate refuses nonfinite/exact-zero scales and machine-level degeneracy relative to training spread and scale. Small but valid scales are not rejected by a universal absolute MAD cutoff. Representability, ties/concentration, influence, and SD/MAD behavior are separate warnings; SD never silently replaces MAD.

Output definitions now distinguish physical source keys, analytical strata, reference design, model, scale, and fallback. Source counts are 520 Primary, 450 reselected strict-V, and 970 in their stratified concatenation. The 970 table is not a unique physical-source union. Model/scale expansion must be declared and cannot be described as additional participant observations. Wide keys permit exactly five task coordinate columns and fail if nonconstant metadata would split a pivot key.

## Bootstrap correction

No empirical bootstrap was run. `bootstrap_protocol_and_limitations.md` separates fixed-transformation resampling from Design-B refit resampling; defines joint multiplicities for overlapping target/reference identities, auxiliary resampling, fixed identity folds, exclusion of every held-out copy, unique draw IDs, variable replicate training counts, and failure types. The historical 1,000/1,000 result remains evidence only for its narrower 52-person no-fold routine. Operational success rates do not establish interval coverage, and dropping undefined replicates conditions the retained distribution.

## Tests, reproduction, and preservation

The standard-library test runner executed 24 named tests containing 34 assertion calls. Corrupted fixtures detect every requested failure class, including incorrect flags, duplicate/missing keys, count-equal identity errors, improper rejection of Design B, Design C mislabeled Reference A, leakage, schema splits, support contamination, M1 age failures, bootstrap-copy leakage, and scale degeneracy. All passed.

A separate fresh-process reconstruction matched all stored scientific results. The execution environment was Python 3.14.0 and NumPy 2.5.2 on Windows 11. Dataset Git remained clean at tag 1.0.6 and commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`.

The immutability check covered 79 declared prior inputs/artifacts, including every file and the ZIP from the prior preflight milestone, named historical scripts, and protected transformation parameter/coordinate artifacts. Every before/after size and SHA-256 matched. This is a scoped claim, not a claim about every workspace file.

## Decisions still requiring explicit review

Before a separate production rebuild:

1. Approve Design B and its candidate fold/fitting-identity hashes, or explicitly select Design A.
2. Approve reuse of the Primary target map and V/F Reference-A parameters for QC sensitivities.
3. Approve M0/M1 and numerical scale-failure semantics.
4. Approve the long/wide keys and 520/450/970 denominator language.
5. Approve the bootstrap protocol if a later milestone will run it.

LNB/CTAP and session-comparability caveats can remain explicitly unresolved for mechanical transformation production, but they must be resolved before making stronger measurement or longitudinal interpretations. No approval is inferred here; use the reviewer template.

**Verdict:** decision-ready specification; explicit review required before rebuild.
