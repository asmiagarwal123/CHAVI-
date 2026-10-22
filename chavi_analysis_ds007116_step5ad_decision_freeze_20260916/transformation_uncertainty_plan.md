# Transformation Uncertainty Plan

## Recommended Approach
**Refit-within-bootstrap** should be the primary approach for handling transformation uncertainty.
In each bootstrap replicate of the candidate primary cohort, the age model (e.g. linear) and scale parameter (e.g. robust MAD) must be refitted.

## Rationale
Using a fixed transformation ignores the sampling variability in the training-reference parameters. Refitting ensures that uncertainty in the intercept, slope, and standard deviation estimate properly widens the final confidence intervals of the profile coordinates.

## Constraints
If small bootstrap samples cause models (especially non-linear splines) to fail to converge or yield a zero scale, those replicates must be discarded and logged, provided the number of valid replicates remains >= 5,000.
