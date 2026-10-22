# Bootstrap and reference-uncertainty protocol

RECOMMENDED SCIENTIFIC PROTOCOL — NOT YET ADOPTED FOR EMPIRICAL EXECUTION.

## A. Conditional bootstrap

Freeze the accepted coordinate table, selected two-visit pairs, folds, parameters, task order, M1 support mask, and estimand definition. For replicate `b`, draw `N` participant identities with replacement; carry both visits and all five tasks with each identity's multiplicity; compute the statistic with multiplicity weights. Never sample visits or tasks separately. Record undefined statistics. Candidate: 10,000 replicates, PCG64 seed recorded in a run contract, equal-tailed percentile limits using NumPy's linear quantile interpolation. Report valid/invalid counts and Monte Carlo uncertainty by rerunning quantile estimation over deterministic batches; do not redraw failures.

This conditions on estimated transformations and selected roles/occasions. It excludes reference-fitting, recruitment, missingness, eligibility, and occasion-reselection uncertainty.

## B. Joint refitting bootstrap candidate

1. Draw 52 original target identities and 57 original auxiliary identities separately with replacement; these fixed roles and counts condition on selection.
2. Attach each target's original fold and both visits. Its target multiplicity is identical in Reference-A fitting and analysis. Use the same auxiliary multiplicity in all five folds; duplicates are frequency weights, never newly independent identities.
3. For fold `f`, remove every copy of every original target identity held out in `f`; fit using remaining target multiplicities plus shared auxiliary multiplicities. Preserve original fold membership. Variable represented fitting counts are expected under unstratified resampling.
4. Re-estimate M0 centers and MAD/SD scales; for M1 re-estimate age coefficients, effective support, and residual scales. Apply each replicate fit to both selected visits.
5. Compute the replicate statistic with target analysis multiplicities. For the initial M1 candidate, retain the original M1-supported identity set and mark a replicate invalid if its refit cannot support those identities; do not pool changing populations.
6. Empty represented folds, too few/distinct ages, zero/numerically degenerate scales, nonfinite values, or undefined statistics are logged once and retained as invalid. No redraw-until-success.

Alternative fold-stratified target resampling guarantees represented folds and conditions on the realized fold counts (11/11/10/10/10); it is a diagnostic comparator, not automatically preferable. Leave-one-target-out, auxiliary-only common reference, and fold-assignment alternatives are future diagnostic designs, not fit here. Shared fold-specific parameters applied to both visits can induce persistence through common location/scale errors; refitting can widen or narrow an interval.

Candidate intervals remain unapproved until ADEMP coverage/failure evidence exists. BCa is not default because small/discrete samples, nonsmooth MADs, and undefined replicates can destabilize acceleration. Percentile limits are a transparent candidate, selected for evaluability—not narrowness. Simulation must compare percentile, basic, and where stable BCa intervals at the same target.

## Deterministic multiplicity fixture

The validator encodes target multiplicities `a=2,b=0`, identical analysis/fit/visit multiplicities, one auxiliary multiplicity map reused in both folds, and exclusion of all copies of each held-out target. Corruptions independently trigger actual validator failures for self-inclusion, decoupled multiplicities, per-fold auxiliary redraws, and independently sampled visits.
