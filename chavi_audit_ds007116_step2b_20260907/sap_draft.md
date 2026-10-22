# CHAVI statistical analysis plan draft — Step 2B boundary

## Status

Decision-ready skeleton only. No final score, reliability, SEM/MDC estimate, or prediction is run in Step 2B.

## Estimand and scientific question

Primary future estimand: within-person change in a frozen, direction-aligned fixed-composition domain profile between two eligible cognitive occasions, with separate reporting of domain level and profile shape. A secondary estimand may describe agreement/reliability after the measurement specification, QC scope, and occasion pairing are approved. Change, practice, occasion, and measurement error must not be conflated.

## Cohort and occasions

Use the pinned ds007116 1.0.6 snapshot and verified Step 1B phenotype payloads. The scheduled ses-1/ses-2 pair is descriptive. The primary repeated-occasion rule should be the first two eligible assessments per participant, with participant-level dependence preserved; report all available eligible pairs separately. Repository session, cognitive occasion, questionnaire occasion, and imaging occasion are distinct. The sub-20812 continuation is retained as a flagged continuation with no separate CNB, not silently treated as a new CNB occasion.

## Fixed construction and missingness

Freeze exact task/field identities before analysis. The current feasibility proxy is LNB/Face/Matrix/ER40/dominant Finger Tapping. Require all five fields for the full profile; a reduced four-domain profile is sensitivity only. Do not substitute a different task across visits in the fixed primary analysis. Report score missingness separately from QC loss and comparability uncertainty. Missing, skipped, invalid, and unresolved QC states are not interchangeable.

## Direction, transformation, and age

Accuracy-like scores are provisionally higher-is-better; speed scores are provisionally lower-is-faster. Any reversal must be frozen with the score manifest. Prefer within-analytic-sample transformations only after direction review; norm-based standardization and age adjustment are optional analyses requiring an appropriate reference and prespecified model. Age, developmental stage, and site/recruitment context must be handled without leakage; cross-fitting is required if a learned adjustment is used.

## Level and shape

Define a level summary only after scale compatibility and weighting are frozen. Define shape as within-person domain contrasts or rank/profile deviations, separately from level. Report task identity and available-domain count alongside every later summary.

## Reliability and agreement

If approved, estimate reliability/agreement for the exact fixed score and each domain using participant-level paired occasions. Report ICC variant and assumptions, within-person SD, SEM, MDC, confidence intervals, and uncertainty due to pair definition and QC policy. Do not infer individual change from a cohort mean.

## Resampling and preprocessing

Specify row/participant exclusions, QC policy, missing-data rule, direction map, transformation, age model, weighting, and outlier handling before resampling. Resampling must respect participant clustering and any repeated-pair structure. Do not tune task selection or transformations on the final outcome.

## SEM/MDC and robustness

Treat SEM/MDC as uncertain until reliability model, scale, occasion interval, and error assumptions are settled. Sensitivities: strict V-only; documented valid/likely-valid; unresolved-QC-inclusive descriptive bounds; scheduled ses-1/ses-2 versus first-two-eligible; full five-domain versus reduced four-domain; accuracy-only versus speed-inclusive specifications; with/without age adjustment only if justified.

## Outcomes and incremental prediction

For each of the five outcomes (`eswan_adhd_inattention_total`, `eswan_adhd_total_score`, `mapssr_total_score`, `im_average`, `em_average`), report baseline outcome, later outcome, baseline any-cognitive score, baseline complete profile, profile plus baseline outcome plus later outcome. Incremental prediction is conditional exploratory work only after profile and outcome timing, missingness, and covariate policy are frozen; it is not performed here.

## Cohort versus individual uncertainty

Cohort change and individual reliable-change decisions require different uncertainty statements. The SAP must report sample size, pair counts, interval limitations, QC loss, and confidence intervals; it must refuse individual-level claims when comparability, reliability, or score direction is unresolved.

## Blockers

Before final composites/reliability/prediction: author confirmation of QC code meanings/scope; exact LEAD task/version and denominator definitions; LNB and CPT formula details; ADT metadata conflict; Trails identity; decision on PCET/AIM/processing-speed placement; occasion handling for continuation; and frozen outcome timing/age policy.
