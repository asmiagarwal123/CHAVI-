# Profile Estimand Hierarchy

For Step 5B Phase 2 reliability analysis, the recommended estimand hierarchy is:

1. **Level/Elevation ($L_{it}$)**: Primary. Represents the simple average of the 5 age-referenced Z-scores.
2. **Centered Shape ($S_{itj}$)**: Primary. The 5 orthogonal components derived by subtracting elevation.
3. **Scatter/Differentiation ($D_{it}$)**: Secondary. Represents the variation across the 5 components for an individual.
4. **Shape-change RMSE ($RMSE^{shape}_{i}$)**: Secondary. Represents the stability of the shape profile over time.
5. **Profile Correlation**: Descriptive only. Included for legacy psychometric comparison, but explicitly demoted due to known instabilities with $k=5$ components.
