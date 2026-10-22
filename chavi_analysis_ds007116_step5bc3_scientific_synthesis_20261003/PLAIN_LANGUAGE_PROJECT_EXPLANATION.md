# Plain-language project explanation

## What was measured

The project follows performance across five score fields: true-positive responses on letter n-back, total correct face-memory responses, total correct matrix-reasoning responses, total correct emotion-recognition responses, and a dominant-hand finger-tapping mean. Higher is treated as better for all five. The repository documentation does not fully resolve the n-back denominator/load or the tapping unit and aggregation, so these descriptions must stay tied to the recorded fields rather than being expanded into stronger psychological or clinical labels.

Because the five scores use different raw scales, they cannot be averaged sensibly as recorded. Each score is therefore expressed relative to a reference group: subtract the reference mean and divide by a reference spread. The primary spread is a robust median absolute deviation (MAD); standard deviation (SD) is a sensitivity analysis. The resulting values are reference-scaled score units, not clinical units or population norms.

For a target participant, Design B estimates the reference conversion without that participant's own reference record in the fold used for them. Other auxiliary reference participants remain available. This reduces self-reference while retaining information needed for stable conversion. It is an application of sample splitting/cross-fitting, not a new cross-fitting method.

## Level and shape

At each occasion, **profile level** is the average of the five transformed task scores. It answers whether the whole profile tends to sit higher or lower. **Centered profile shape** subtracts that level from each task score. It answers how tasks differ relative to that person's own average at that occasion. A person can change level with little shape change, or change the pattern among tasks with little average change.

Three planned summaries were calculated:

- **ICC(A,1)** measures absolute agreement of profile level across the two occasions. It penalizes systematic occasion differences as well as rank changes; it is not a correlation of the five-task shapes.
- **Mean level change** averages occasion 2 minus occasion 1 profile level. Positive values mean higher later performance in the implemented reference-scaled units, but cannot separate development, practice, selection, measurement, or other causes.
- **RMS centered-shape displacement** pools squared changes in all five centered task coordinates, then takes a square root. It is nonnegative and includes measurement variability; a positive interval alone does not prove genuine person-specific change.

The descriptive within-person profile correlation summarizes similarity in centered pattern, but correlation removes level and scale. It is not evidence that an individual's profile is reliable.

## What P2 and P3 ask

P2 resamples the 52 participant pairs while holding the fitted reference transformation and transformed coordinates fixed. P3 resamples participant identities and refits the reference transformation in every bootstrap draw. Thus P3 propagates more of the estimated-reference workflow. The realized P2 and P3 interval widths can be described, but their difference is not a test of superiority and is not a pure estimate of “reference variance.”

Simulations can evaluate interval coverage because the data-generating truth is known. The empirical dataset has no revealed true ICC, change, or displacement, so 999 valid empirical draws establish computational availability—not correct 95% coverage.

## What the evidence says

For the primary 52 pairs using M0/MAD, level agreement was 0.619; mean level change was 0.366 transformed units; and pooled RMS centered-shape displacement was 1.002 transformed units. The P2/P3 percentile intervals were respectively 0.373–0.786 and 0.380–0.787 for ICC; 0.182–0.557 and 0.178–0.547 for mean change; and 0.811–1.198 and 0.801–1.372 for RMS displacement. All used 999 valid draws.

Sensitivity estimates change when the scale estimator, model/support, eligibility rule, or pair selection changes. Those analyses are informative robustness descriptions, but their differences do not isolate single causal mechanisms.

In the repaired confirmatory simulations, P3 improved RMS percentile coverage over P2 in continuous S1 (0.9175 versus 0.803), yet remained below the nominal 0.95 target. In rounded/tied S5, P2 was available in 1,994/2,000 outer replicates and available-and-covering in 0.916 overall; P3 was available in only 1,260/2,000 and available-and-covering in 0.6025 overall. Conditional coverage alone therefore hides an important failure/availability tradeoff. The real dataset is not established to be either S1 or S5.

## Completion and next step

The transformation, estimands, simulations, empirical execution, independent numerical validation, scientific synthesis, tables, and figures are complete. Manuscript drafting can begin now if its claims stay narrow. The next action is to resolve the remaining measurement metadata—especially n-back denominator/load, tapping units/aggregation, task-version comparability, and session timing—or explicitly preserve those limitations in the manuscript.

