# Ipsative / Centering Analysis — Correction to Step 5A-D

## Correction C9: Centered shape components are NOT five orthogonal dimensions

The centered shape coordinates S_itj = Z_itj - L_it sum algebraically to zero
for any profile:

    sum_j S_itj = sum_j Z_itj - 5 * L_it = 5*L_it - 5*L_it = 0

This is an algebraic identity, not an empirical finding.

The five centered components therefore lie in a (k-1) = 4-dimensional
subspace of R^5. They cannot be treated as five independent dimensions for
any inferential purpose.

## Consequences
1. Scatter D_it is correctly defined on the full five-component vector.
2. Shape-change RMSE is correctly defined component-wise.
3. Profile correlation between centered vectors is interpretable as a
   directional agreement measure, but with k=5 it is unstable.
4. The five centered deviations must NOT be treated as five independent
   regression predictors or five confirmatory tests.
5. Later simulation must account for this dependency structure.

## What Step 5A-D-R does NOT change
- The formula for S_itj is unchanged.
- The formula for D_it is unchanged.
- The formula for RMSE_shape_i is unchanged.
- No numerical result is affected — the correction is terminological only.

## Machine-readable confirmation
centered_shape_constraint: "sum_j S_itj = 0 exactly (algebraic identity)"
effective_dimensionality_of_shape: 4
not_five_independent_dimensions: true
