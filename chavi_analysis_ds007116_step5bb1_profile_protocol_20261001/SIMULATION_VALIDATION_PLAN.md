# Future ADEMP simulation-validation plan

RECOMMENDED SCIENTIFIC PROTOCOL — NOT YET ADOPTED FOR EMPIRICAL EXECUTION.

## Aims

Evaluate bias, RMSE, interval coverage/width, invalid-estimate and invalid-replicate rates, false-positive behavior under null stability, and sensitivity to transformation/reference uncertainty for the exact proposed statistics. This is method comparison, distinct from the completed deterministic software demonstration.

## Data-generating mechanisms

Generate a superpopulation with five task-specific discrete or continuous source scores, explicit auxiliary and target roles, age, folds, two clustered occasions, latent person level and four-dimensional shape, occasion shift, correlated task noise, and reference-induced dependence. Cross scenarios: no stable person shape; stable shape plus noise; stable level/unstable shape; mean shifts with stable ordering; discrete/tied/ceiling scores; small/zero MAD; heavy tails/influential observations; linear versus nonlinear age; target/reference age mismatch; and reference/target sizes including 57/52 and larger benchmarks. Separate stable differences, genuine change, occasion shifts, correlated noise, shared-reference effects, and nonlinear/support failures factorially where feasible.

## Estimands and truth

Define truth as an analytic population functional when derivable or as a preregistered, independently computed limit using a very large reference population—not the realized sample estimate. Truths include population level ICC(A,1) under the specified two-occasion model, population mean level change, RMS centered-shape displacement, and descriptive trace association. Undefined population cases remain explicit.

## Methods

Compare fixed-parameter conditional bootstrap, unstratified identity-linked joint refitting, fold-stratified joint refitting, and interval types (percentile/basic; BCa only when defined). Compare M0/MAD, M0/SD and fixed-support M1. Evaluate auxiliary-only and leave-one-target-out references as diagnostic methods.

## Performance measures

For each scenario report bias, relative/absolute bias as appropriate, RMSE, empirical 95% coverage, mean/median width, lower/upper tail miss rates, invalid point/replicate/run rates, and null false-positive rate for any adopted hypothesis. Report Monte Carlo standard errors: `sqrt(p(1-p)/R)` for proportions and replicate-based SEs for means. Choose `R` from a prespecified maximum MCSE (e.g. <=0.005 for coverage near .95 requires at least 1,900 successful runs; use a larger round number after pilot failure rates). No claim of power or adequate N=52 precision is made here.
