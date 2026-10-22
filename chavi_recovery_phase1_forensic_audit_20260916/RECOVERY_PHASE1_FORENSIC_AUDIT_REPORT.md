# CHAVI Recovery Phase 1 — Forensic Audit

Date: 2026-09-16. Scope: read-only forensic audit; no profile level, shape, scatter, ICC, simulation, threshold, or Evidence Engine analysis was performed.

## Result

The last unquestionably trustworthy boundary is **Step 5A measurement specification / Step 5A-D-R2 evidence only**, limited to upstream cohort-definition evidence. Step 5A-F approval is an approval artifact, not proof that later implementation is correct. All transformed-data and later validation artifacts require regeneration or are reference-only.

The central finding is a lineage break: Reference A is 109 participants, so five participant folds must have training sizes 87 or 88 (folds of 22/22/22/22/21). Files reporting 98 are consistent with 11-person held-out folds from 109; files reporting 41–42 are consistent with fitting the 52-person primary cohort and therefore use the wrong reference population.

## Critical/high issues

- CRITICAL: 109-person Reference A versus 52-person fitting is present in competing implementations.
- CRITICAL: M1 residual scale/support semantics are not fully present in the frozen JSON and are introduced later without a clean amendment chain.
- HIGH: 120-row wide output mixes cohort metadata; expected primary/V-only outputs are 104/90 and explicitly stratified combined output is 194.
- HIGH: 540, 970, and 970-derived stratified rows have different denominators; “canonical 970 rows” is not an acceptable unqualified description.
- HIGH: extrapolation counts are denominator-dependent and not reconciled by stable participant/task keys.
- HIGH: claimed independent validators/tests are not sufficient where they reuse production parameters, outputs, or copied helpers.

## Verdicts

Reference A: the approved definition is 109 participants × 5 earliest complete synchronized task rows = 545 rows; the 52-person fit is invalid for Reference A. Transformation implementation: no existing implementation matches the full approved intent with independently demonstrated lineage. Independent validation: not established. Test quality: assertions exist, but coverage is not independent of the known Reference A error and mixed-strata/extrapolation risks.

Existing artifacts were not modified. Baseline and after-audit hashes are recorded in recovery_phase1_provenance.json; the only new files are inside the recovery directory.

Audit limitations: recursive discovery encountered access-denied pytest cache directories; those paths are recorded as inaccessible where encountered.
