# CHAVI Source-Based Transformation Recovery Preflight and Contract Repair

**Date:** 1 October 2026  
**Milestone directory:** `chavi_recovery_preflight_20261001/`  
**Verdict:** **READY AFTER EXPLICIT CONTRACT DECISIONS.**  
**Scope stop:** no transformation parameters, coordinates, profile inference, simulations, reporting thresholds, prediction, or UI were produced.

## Executive result

The reusable source boundary is available and internally coherent through Step 3B source observations, Step 5A synchronized-cohort evidence, and Step 5A-D-R2 decision evidence. Step 5A-F is usable as an approval-intent record, but not as a complete executable contract. Existing Step 5B-A/R2/R3 artifacts remain quarantined and were not used as calculation inputs.

Independent reconstruction from `chavi_audit_ds007116_step3b_20260909/task_observations_long.csv` and `assessment_occasion_mapping_step3a.csv` reproduced all expected source cohorts by identity and count:

| Cohort | Participants | Occasions | Task rows | Fresh result |
|---|---:|---:|---:|---|
| Reference A | 109 | 109 | 545 | PASS |
| Primary V/F | 52 | 104 | 520 | PASS |
| V-only sensitivity | 45 | 90 | 450 | PASS |

The 50/52/53 reconciliation also reproduced exactly. The two profile-first participants not in the aligned-50 task-pair set are `sub-20259` and `sub-20494`; the task-pair-intersection participant excluded from the profile-first 52 is `sub-21035`.

The preflight found a previously hidden fold-identity conflict. Applying the frozen wording literally with NumPy 2.5.2—sort 109 Reference-A IDs, `default_rng(42).permuted`, then assign permutation index modulo five—produces the required held-out counts 22/22/22/22/21 and training counts 87/87/87/87/88, but does not reproduce Recovery Phase 1's expected identity lists. Recovery's lists exactly match unpermuted sorted round-robin assignment. Only 6, 2, 2, 4, and 4 held-out identities overlap in folds 0–4 between the alternatives. This materially changes every fold-specific parameter and support bound.

Therefore the source and environment are sufficient, but production is not authorized until the exact fold identity map and the remaining contract amendments are explicitly reviewed and approved.

## Evidence classification

- **Freshly verified:** calculations executed in this milestone from source or immutable metadata.
- **Historical document finding:** statement found in an earlier artifact but not rerun here.
- **Proposed amendment:** a defensible exact rule offered for approval; not historically approved.
- **Unresolved:** evidence is insufficient or contradictory; a decision is required.

## 1. Evidence and environment preflight

### Workspace and version control

The actual workspace was available at `C:\Users\asmi\Desktop\Projects\CHAVI`. The CHAVI root has no `.git`, so project commit/diff history is unavailable. The nested dataset repository was freshly checked with a command-local safe-directory override:

- commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`;
- tag `1.0.6` at HEAD;
- branch status `main...origin/main`;
- clean porcelain status.

Source: fresh Git calls recorded in `preflight_results.json`.

### Input inventory and hashes

`input_artifact_manifest.csv` records paths, byte sizes, and SHA-256 hashes for all eight supplied handoff documents and the governing dataset, Step 1B, Step 3B, Step 5A, R2, Step 5A-F, and Recovery Phase 1 artifacts. All declared inputs existed.

The canonical Step 3B task source hash freshly matched the frozen-contract value:

`8b435d4b23d0b5f70b3c56ade4215d215028426dbdb46eaaf8daaa3cd0dc1978`.

All 41 staged phenotype files were freshly hashed and sized against `chavi_audit_ds007116_step1b_20260907/retrieval_manifest.csv`; no mismatch occurred. Historical absolute staging paths in that CSV were ignored in favor of the current relative staging directory.

### Interpreter and dependencies

The base interpreter is Python 3.14.0 but lacks the scientific stack and pytest. No environment declaration exists in the project. An isolated environment at `C:\tmp\chavi_preflight_numpy_env` was created with only NumPy 2.5.2 to reproduce the exact RNG algorithm named in the historical contract. It did not modify the project interpreter.

Source: `environment_and_reproduction.md`, `isolated_environment_requirements.txt`, and `preflight_results.json`.

### Script inspection and mutation boundary

The new script was inspected and syntax-compiled before execution. It writes only to this milestone directory, uses read-only Git calls, and never imports quarantined production code. Step 5A outputs are read only after independent reconstruction for comparison. No historical file changed.

Several historical transformation scripts hard-code `C:\Users\asmi\Desktop\Projects\CHAVI`; earlier audit text also references `C:\Users\asmi\Desktop\Projects\ML Projects`. The new script uses paths relative to itself.

## 2. Independent source and cohort reconstruction

### Source rules applied

The reconstruction selected only the five exact Step 3B fields:

`cnb_lnb_mcr`, `cnb_cpf_cr`, `cnb_pmat_cr`, `cnb_er40_cr`, and `cnb_ctap_dom`.

For Primary/Reference-A eligibility, every selected score had to be finite and its exact raw QC code had to be `V` or `F`. Each of the five pinned task dictionaries was freshly inspected: `V` means Valid and `F` means Likely valid with a limited/mild-to-moderate problem. Step 3B eligibility flags matched this direct reconstruction with zero mismatches. V-only required exact `V` for every task.

The source contained 1,095 rows and 1,095 unique participant/session/task keys. There were no duplicate keys, selected-field/table mismatches, or eligibility discrepancies.

`sub-20812/ses-2` was independently identified from the occasion map as a continuation and excluded from new-occasion construction. All retained occasions remain only “candidate comparable by session label”; exact assessment timing, administration conditions, and task-version equivalence remain unresolved.

Sources: `task_observations_long.csv`, `assessment_occasion_mapping_step3a.csv`, five dataset dictionaries, `qc_dictionary_verification.csv`, and `preflight_results.json`.

### Identity results

`source_cohort_reconciliation.csv` gives one row for each of 132 registered participants, with source presence, V/F and V-only complete sessions, Reference-A session, Primary/V-only selected sessions, task-pair membership/alignment, and excluded continuation sessions.

Fresh results:

- 132 registered identities;
- 131 represented in Step 3B task source;
- 176 complete synchronized V/F occasions;
- 109 Reference-A identities and 545 unique task rows;
- 52 Primary identities, 104 occasions, 520 rows;
- 45 V-only identities, 90 occasions, 450 rows.

The independently reconstructed Primary and Reference-A identity sets exactly match the later Step 5A manifests when those manifests are used only as comparison targets.

`reference_cohort_manifest.csv` records every Reference-A participant/session/task source key, raw/numeric value, exact QC code and meaning, source row reference, session age, comparability status, and candidate fold.

### 50/52/53 reconciliation

The preflight reconstructed task-specific first-two V/F pairs directly from Step 3B rather than reading Step 4B pair results:

- 53 identities have a separately eligible pair for every task;
- 50 use the same selected session pair across all five tasks;
- 52 have two jointly complete synchronized five-task V/F occasions;
- `sub-20259` and `sub-20494` are added by the profile-first construction relative to aligned 50;
- `sub-21035` is in the five-task pair intersection but lacks two jointly complete V/F profile occasions.

This confirms that 50, 52, and 53 are different constructions, not contradictory counts.

## 3. Deterministic reference folds

### What historical artifacts actually establish

The R2 candidate/frozen wording states “NumPy RNG seed=42 permutation of sorted participant list; round-robin assignment.” However, `run_step5adr2.py` constructs `pts_arr` from `pts_2plus`, the 52-person Primary cohort. Its approval evidence therefore reports 11/11/10/10/10 folds. It never demonstrated the same algorithm on Reference A's 109 identities.

Recovery Phase 1 correctly requires 109-person folds and 87/88-person training sets, but its `reference_a_fold_expected_counts.csv` identity lists are not the output of the stated seed-42 permutation.

### Fresh reconstruction

The preflight applied the literal wording to the independently reconstructed 109 identities using NumPy 2.5.2. It verified:

- each Reference-A identity appears in exactly one held-out fold;
- held-out counts 22/22/22/22/21;
- training counts 87/87/87/87/88;
- zero held-out/training identity overlap;
- all Primary and V-only participants map to Reference A;
- repeated execution in the same declared environment gives identical assignments.

`participant_fold_manifest.csv` emits every participant's candidate fold, Reference/Primary/V-only membership, held-out and training identity lists, and newline-canonicalized SHA-256 identity hashes.

### Unresolved conflict

`fold_algorithm_comparison.csv` proves:

- literal seed-42 permutation does not match Recovery Phase 1 identities in any fold;
- unpermuted sorted round-robin matches all Recovery Phase 1 identities exactly.

This requires explicit approval. The preflight recommends preserving the literal frozen algorithm wording and approving its newly emitted 109-person identity hashes, but does not label that choice approved.

## 4. Transformation contract repair

`step5ba_rebuild_specification_candidate.json` is machine-readable and explicitly marked `candidate_not_approved`. `contract_gap_and_decision_register.csv` separates existing approved values, upstream evidence, proposed amendments, alternatives/consequences, and decisions needed.

### Supported boundaries

- Exact five fields and positive direction.
- V/F Primary and V-only sensitivity QC.
- No imputation and complete synchronized occasions.
- Reference A 109 and Reference B 52 definitions.
- M0 primary, M1 sensitivity, M2 excluded.
- MAD primary and SD sensitivity at a high level.
- P3 principle: M1 unsupported outside age support; retain a separately labelled M0 coordinate.
- Participant resampling, refit-within-bootstrap intent, 5,000-valid target and 10,000-attempt maximum at a high level.

### Proposed exact amendments

- M0 center: arithmetic mean of direction-adjusted training scores.
- MAD: `median(abs(v-median(v))) / 0.6744897501960817`.
- SD: sample standard deviation, `ddof=1`.
- M1: OLS with intercept on Step 3B `session_age`; residual divided by training residual MAD; SD sensitivity.
- Support: inclusive fold-specific finite training-age minimum/maximum.
- P3: `m1_coordinate` remains null when unsupported; M0 is stored under explicitly M0-labelled fallback fields.
- Explicit long/wide keys include analytical stratum, model, and scale.
- Primary and V-only files remain separate; a 970-row concatenation is only an explicitly stratified view.

### Unresolved decisions

1. Exact 109-person fold identity algorithm/map.
2. Numerical zero/near-zero refusal threshold.
3. Formal approval of M1 residual-scale/support/fallback semantics.
4. Formal approval of output keys and combined-view semantics.
5. Exact bootstrap overlap, fold, duplicate-draw, and failure behavior.

### Bootstrap evidence correction

The R2 feasibility report says Reference A was reconstructed in each replicate, but its code samples `pts_2plus`, which contains only 52 Primary participants, then retrieves their rows from `df_ref_a`. It also states folds were not applied. Thus 1,000/1,000 success is a historical feasibility result for a 52-person subset procedure, not evidence that the proposed 109-person cross-fitted refit bootstrap is feasible.

The candidate contract proposes an overlap-preserving stratified participant bootstrap: resample analysis-stratum Reference-A identities and use the same multiplicities in both reference and analysis, while separately resampling the remaining Reference-A identities. Original approved identity folds remain fixed; duplicate draws receive draw IDs and share the original participant fold. This is proposed, not approved, and must be feasibility-tested after approval.

## 5. Independent validation design

`independent_validation_plan.md` specifies a validator that rebuilds expected source rows, cohorts, folds, centers, scales, OLS parameters, predictions, residuals, support flags, and coordinates before opening production outputs. It defines exact identity/count invariants, floating tolerances, edge cases, deterministic hashes, failure criteria, and tests for every known historical failure.

The crucial safeguard is identity-based validation. A correct-looking 545-row manifest is insufficient: each parameter row must carry and match the approved 87/88-person training identity hash.

## 6. Testing performed

Fresh checks performed in this milestone:

- script mutation review and syntax compilation;
- dataset Git commit/tag/clean verification;
- 41 staged-payload hash and size comparisons;
- five dictionary V/F meaning checks;
- Step 3B uniqueness/field/QC eligibility checks;
- independent cohort and 50/52/53 identity reconstruction;
- seed-42 NumPy fold reconstruction and repeatability;
- comparison against Recovery Phase 1 fold identities;
- 10/10 unit tests in `test_preflight.py`;
- JSON and CSV parse validation;
- package inventory/hash validation.

Passing upstream or preflight tests do not validate future production coordinates. The full independent validator described above remains a required gate for the subsequent rebuild.

## 7. Readiness verdict

**READY AFTER EXPLICIT CONTRACT DECISIONS.**

Source access is not blocked. The exact dataset and payloads are available and verified. The isolated environment was sufficient for the bounded reconstruction. Cohort identities and counts are ready for reuse.

Production is not yet authorized because fold identities conflict and the M1, near-zero-scale, output-schema, and bootstrap amendments are not approved. Resolve PF-001 through PF-015, sign/hash the amended candidate contract and chosen fold manifest, and then start a separate clean Step 5B-A rebuild. Do not use quarantined parameters or coordinates.

In plain language: the raw ingredients and participant groups are sound, but the recipe still contains a few consequential choices that must be explicitly agreed before cooking the final transformed data.
