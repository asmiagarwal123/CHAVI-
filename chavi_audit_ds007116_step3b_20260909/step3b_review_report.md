# CHAVI Step 3B review report

## Outcome

Step 3B created an analysis-preparation package and a concrete statistical analysis plan draft using the Step 3A executable specification. It reused the 41 verified Step 1B phenotype payloads from OpenNeuro ds007116 snapshot 1.0.6 at commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`. No payload was redownloaded, no raw payload was modified, and no statistical inference or prediction was run.

## Created preparation data

- `task_observations_long.csv`: 1,095 source task rows for the five exact candidate fields, including raw values, numeric parses, QC codes/meanings, policy eligibility/reasons, missingness, age/timing caveats, comparability and source-row references.
- `paired_task_observations.csv`: 2,384 task-specific rows under first-two eligible and complete scheduled rules, with both raw/numeric observations, policy reasons, intervals and source references.
- `paired_profile_manifest.csv`: 433 participant/policy/pair-rule records requiring the same five task identities at both occasions.
- `outcome_observations_long.csv`: 1,115 rows for the five previously audited outcome fields with source, session, raw/numeric value, missingness and timing fields.
- `candidate_prediction_cohort.csv`: 3,300 labelled participant/outcome/policy rows separating baseline cognitive, complete-profile, baseline outcome, later outcome and candidate-intersection status. The follow-up rule is explicitly `PROPOSED—NOT APPROVED`; alternative later observations remain in the long outcome table.

## Reconciliation and verified benchmarks

The fixed-profile counts did not change from Step 3A:

| Policy | Eligible occasions | Participants | Repeated participants | First-two pairs | Complete scheduled pairs |
|---|---:|---:|---:|---:|---:|
| Unfiltered observed | 202 | 123 | 63 | 63 | 60 |
| Documented valid/likely-valid | 176 | 109 | 52 | 52 | 48 |
| Strict documented V-only | 157 | 101 | 45 | 45 | 39 |

Every benchmark row in `cohort_reconciliation.csv` reconciles. The Step 3B package does not alter eligibility rules. The prior Step 3A correction remains the reason older Step 2B counts differed: `sub-20259/ses-1` and `sub-20350/ses-1` were admitted by the old substring handling of `Not Valid`; exact dictionary mapping classifies them as invalid and excludes them. The affected-record and rule-level trace is preserved in Step 3A `eligibility_change_trace.csv` and `implementation_closure.md`.

The recommended candidate prediction intersections are 52 E-SWAN inattention, 50 E-SWAN total, 45 MAPS-SR, 45 intrinsic motivation and 42 extrinsic motivation. These are cohort availability counts under the proposed ses-1/earliest-later rule, not model results or evidence of predictive power.

## Independent verification performed

The preparation script and focused checks verified:

- Step 3A fixture tests pass.
- All 41 staged payloads are reused and the pinned dataset commit/status remain unchanged before and after preparation.
- No duplicate participant/session/task/selected-field analytical keys occur.
- Pair keys retain participant identity; paired task and profile records are not treated as independent participants.
- Profile manifests retain identical five task/field identities across occasions and do not substitute same-domain tasks.
- A configured QC policy change changes synthetic eligibility as intended.
- The `sub-20812/ses-2` continuation remains a flagged continuation and cannot create a new CNB occasion.
- Pair, observation, profile, outcome and candidate counts reconcile in `cohort_reconciliation.csv`.

Hashes, input roles, output hashes, software information, test names and the dataset state are recorded in `provenance_step3b.json`.

## What remains before analysis

Scientific review is still required for exact task/version equivalence, score-specific QC scope, LNB denominator/load meaning, direction and common reference choices, primary pair rule, age estimand/support, primary outcome and follow-up timing, ICC convention, shape representation, multiplicity, precision simulations and claim-specific reporting tolerances. These are registered in `decision_register_step3b.csv`; each proposed choice is marked `PROPOSED—NOT APPROVED`.

Step 3B deliberately did not calculate standardized scores, composites, ICCs, SEM/MDCs, fitted age effects, predictive models, imputation, diagnostic classifications or Evidence Engine decisions.

## Review files to share

Share these files for scientific review:

1. `sap_step3b_draft.md`
2. `decision_register_step3b.csv`
3. `task_observations_long.csv`
4. `paired_task_observations.csv`
5. `paired_profile_manifest.csv`
6. `outcome_observations_long.csv`
7. `candidate_prediction_cohort.csv`
8. `cohort_reconciliation.csv`
9. `analysis_data_dictionary.csv`
10. `provenance_step3b.json`

The executable preparation script and `reproduction_and_tests.md` should accompany the review package.
