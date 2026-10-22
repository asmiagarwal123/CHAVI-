# Bootstrap Protocol and Limitations

No empirical bootstrap was run in this milestone. The historical 1,000/1,000 result sampled only the 52 Primary participants, retrieved their Reference-A rows, and did not exercise cross-fitted folds. It is computational evidence for that narrower routine, not evidence for Design A or B refit inference and not evidence of confidence-interval coverage.

## A. Fixed-transformation resampling

- Freeze the approved fold map, fitted parameters, support bounds, and selected complete-case cohort.
- Within each declared analytical stratum, sample participant identities with replacement; retain both visits and all five tasks as one participant cluster.
- Give every draw a unique `draw_id`; duplicated identities remain duplicated clusters.
- Do not resample or refit the 109-person reference. Target/reference overlap is therefore conditioned on the already fitted transformation.
- Fold identity is fixed only as provenance; no fitting occurs in a replicate.
- Report stratum sample size as the fixed number of participant draws (52 Primary, 45 reselected strict-V, or 41 fixed-pair strict-V).

This estimates downstream sampling variability conditional on the selected cohort and fitted transformation. It omits reference-parameter uncertainty.

## B. Refit-transformation resampling under recommended Design B

- Resampling unit is participant identity, with all retained records travelling together.
- For the Primary analysis, jointly sample the 52 overlapping target/reference identities with replacement. The same draw multiplicity must be used in target and reference roles. Separately sample the 57 auxiliary Reference-A identities with replacement.
- Preserve the approved original identity-to-fold map; do not regenerate folds opportunistically. Every copy of one identity has its original fold and a unique `draw_id`.
- For a held-out fold, exclude **all copies** of every held-out target identity from fitting. Retain sampled copies of auxiliary identities. Duplicate target copies in other folds and duplicate auxiliary copies contribute according to their draw multiplicities.
- Variable unique-identity and row counts are expected after resampling; do not require original 98/99 counts inside a replicate.
- For reselected strict-V or fixed-primary-pair strict-V analysis, target eligibility changes but the V/F Reference-A fitting design remains fixed. Reuse the Primary target-fold mapping and declare how non-Primary sensitivity targets are handled before execution; the recommended current contract produces sensitivity coordinates only where a Primary fold exists and does not invent a new fitting population.

If a later reviewer instead approves Design A, resample all 109 Reference-A participant clusters jointly and exclude every sampled copy of identities in the fixed held-out reference fold. That is a different inferential procedure and must not be mixed with Design B results.

## Failure taxonomy

Record failures at task/fold/model/scale/stratum/replicate granularity:

- `parameter_fit_failure`: insufficient effective training identities, nonfinite inputs, rank deficiency, or failed fit.
- `scale_failure`: exact, nonfinite, or numerical degeneracy under the approved scale policy.
- `unsupported_m1_observation`: missing/nonfinite target age or age outside inclusive training support; M0 may remain valid.
- `missing_coordinate`: source score missing/nonfinite or required parameter unavailable.
- `undefined_later_estimand`: coordinates exist but the later statistic is undefined.
- `computational_failure`: exception, resource failure, or corrupted state.

An unsupported M1 row does not invalidate an otherwise valid M0 replicate. Never coerce an undefined coordinate or estimand to zero. Dropping failed/undefined replicates conditions the retained distribution and must be reported; a high valid-replicate percentage does not establish interval coverage.

## Feasibility versus validity

The historical target of 5,000 valid replicates from at most 10,000 attempts and the 95% operational threshold may be carried forward only as proposed computational monitoring. Statistical validity, bias, and coverage require later estimand-specific review and simulation; they are outside this milestone. All bootstrap inference is conditional on the selected complete-case cohort unless a different missing-data estimand is approved.

Synthetic tests in this package check draw IDs and held-out-identity leakage only. They estimate no empirical profile effect and calibrate no threshold.
