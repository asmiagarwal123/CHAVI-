# Step 5A-D Review Report

## Scope
This phase conducted the supervisor decision freeze and transformation-feasibility diagnostics without modifying existing artifacts or beginning Step 5B execution.

## Cohort Verification
The profile-first cohort was independently reconstructed from Step 3B outputs. The 176 complete synchronized occasions, 109 participants with >=1 occasion, and 52 candidate primary participants were perfectly reproduced.

## Grouped Cross-Fitting
A 5-fold grouped cross-validation strategy was implemented, grouping strictly by `participant_id` to prevent data leakage between folds and ensuring all occasions for a given participant remain in the same fold.

## Age Model Feasibility
Three candidate age models were evaluated: Model 0 (intercept-only), Model 1 (linear), and Model 2 (limited nonlinear, df=3 natural spline). The diagnostics reveal the out-of-fold RMSE for all three models across the five tasks. The differences in RMSE are minimal, meaning complex nonlinear models are not scientifically justified given the sample size, and a linear model or intercept-only model is preferred.

## Scale and Extrapolation
Extrapolation outside the training age boundaries is risky due to data sparsity at the tails. The policy to "flag and restrict" extrapolated predictions is recommended.

## Next Steps
The decision matrix contains all blockages that must be explicitly resolved by a supervisor. The transformation contract is drafted but marked `not_ready` with the blocker `pending_human_approval`. Step 5B is NOT started.
