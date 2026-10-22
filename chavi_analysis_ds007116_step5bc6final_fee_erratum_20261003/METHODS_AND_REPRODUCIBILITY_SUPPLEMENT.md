# Methods and reproducibility supplement

## Frozen empirical analysis

The empirical analysis uses two occasions and five oriented fields: letter n-back true positives, face-memory total correct, matrix-reasoning total correct, emotion-recognition total correct, and dominant-hand finger-tapping mean. The primary target set has 52 earlier/later pairs and the reference set has 109 participants. Cross-fitting assigns targets to folds of 11/11/10/10/10; the fold fit uses 98/98/99/99/99 eligible reference participants and excludes a target's own reference record. M0 uses the MAD scale `median(abs(y-median(y)))/0.6744897501960817`; the SD sensitivity uses sample SD with `ddof=1`.

Level is the five-coordinate mean. Centered shape is each transformed coordinate minus level. Endpoints are ICC(A,1) over two occasions, mean level change, and pooled RMS centered-shape displacement `sqrt(sum_i,sum_j(delta q)^2/(5n))`. The profile correlation is descriptive only, under the frozen degeneracy rule. The primary interval evaluation has 999 P2 and P3 bootstrap draws per endpoint/method; all twelve cells have 999 valid draws. Percentile and basic 95% intervals use linear quantiles.

## Repaired simulation contract

P1 is oracle conditional, P2 retains the fitted transformation, P3 resamples identities and jointly refits, and P4 jointly refits while preserving original folds. Each attempted bootstrap uses 999 draws; an interval needs at least 950 valid draws, at least 20 observations in each 2.5% tail, a finite point estimate, and a defined truth. No redraw substitutes a failed draw. Availability is available/attempted; conditional coverage is covered/available; available-and-covered is covered/attempted; width is summarized only for available intervals.

The repaired pilot has 100 outer replicates for S1-S6. The confirmatory evaluation has 2,000 outer replicates only for continuous S1 and rounded/tied S5. S1 has level and shape cross-occasion correlation 0.8; S2 sets shape correlation to 0; S3 adds a common +0.5 shift; S4 adds a +0.5 first-Helmert shape shift; S5 rounds to nearest integer with ties-to-even; S6 puts probability 0.6 at each task mean and makes MAD structurally undefined. Base means are 10, 12, 14, 16, 18; level variance is 0.5, shape covariance is 0.5I, and error covariance is 0.5 times a matrix with entries `0.3^distance`. The master seed is 20261002 with PCG64DXSM streams. S6 has undefined MAD truth but defined SD truth; S5 mean-level truth is exactly zero by symmetry.

## Provenance and public package scope

`tables/empirical_all_planned_point_estimates.csv`, `tables/empirical_primary_intervals.csv`, and `tables/empirical_profile_correlation_summary.csv` reproduce public aggregates derived from C2 execution. `tables/simulation_synthesis_all_prespecified.csv`, `tables/simulation_failure_reason_summary.csv`, and `tables/confirmatory_all_endpoint_tradeoffs.csv` reproduce repaired B3-R-derived public aggregates. Figures are public aggregate figures with their plotting data. This package intentionally contains no raw records, participant IDs, or code-deposit claim.

`code/validate_c6.py` generates `validation/checks.json`. It recomputes interval widths and ratios from unrounded C2 inputs, verifies selected B3-R counts, tests ZIP integrity and member paths, compares copied-file hashes with sources, records upstream package hashes, and scans public outputs for participant-ID patterns. It does not rerun the scientific pipeline.
