# Profile estimand specification (draft; no values computed)

After a future approved task-wise transformation produces comparable coordinates, let the five-dimensional occasion vector be `Z_it = (Z_it1, ..., Z_it5)` for participant `i` and occasion `t`. Step 5A does not create these values.

- Elevation: `L_it = (1/5) * sum_j Z_itj`. This is a level/elevation estimand in standardized task units; it is not a clinical severity score.
- Centered shape: `S_itj = Z_itj - L_it`. This is a within-occasion relative configuration; it deliberately removes common elevation.
- Scatter: `D_it = sqrt((1/5) * sum_j S_itj^2)`. This describes dispersion around that occasion's elevation; it is nonnegative and depends on the chosen task coordinates.
- Shape change: `RMSE_shape = sqrt((1/5) * sum_j (S_i2j - S_i1j)^2)`. This is absolute centered-vector change, not a reliability coefficient.
- Shape similarity: the Pearson correlation of the five centered components across occasions is a descriptive/sensitivity measure only; with five components it is discrete/fragile and undefined when a centered vector has zero variance.

Inputs must be the same five exact task fields, in the registered order, with units explicitly documented after transformation. Raw source scores are heterogeneous and must not be averaged across tasks as if commensurate. Limits: all profile estimands require five finite transformed components; shape/scatter measures are mathematically sensitive to component variance, ties, shared elevation, and error covariance. Individual-level interpretation requires separate uncertainty and beyond-error methods, which are not performed here.
