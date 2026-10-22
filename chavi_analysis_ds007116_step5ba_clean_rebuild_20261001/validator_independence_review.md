# Validator Independence Review

The validator is computationally independent, not an external human review.

- `independent_validator.py` does not import `run_clean_rebuild.py`, `prepare_contract.py`, or any quarantined transformation module.
- It reconstructs source eligibility, cohorts, and Design-B folds from canonical Step 3B sources and immutable contract rules.
- It uses a centered-covariance OLS calculation and independently implemented sorted median, MAD, and two-pass SD. Production uses NumPy least squares for M1 and separate production helpers.
- It writes `independent_expected_parameters.csv` and `independent_expected_coordinates_long.csv` before opening production parameter or coordinate tables.
- Production outputs are then used only for exact-field, nullness, and tolerance comparisons.
- Shared dependencies are Python, NumPy, the frozen contract/schema, and immutable source data. No substantive production helper is shared.

Static import inspection and the runtime validation record confirm `production_module_imported=false`. This establishes separate code paths; it does not claim an independent person or institution performed the review.
