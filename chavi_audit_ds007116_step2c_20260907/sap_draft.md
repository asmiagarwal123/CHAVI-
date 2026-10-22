# CHAVI SAP draft — Step 2C review boundary

## Objective hierarchy

**Primary:** longitudinal dependability/agreement of prespecified cognitive measurements and individualized profile shape, distinguishing overall profile level from relative within-person patterns.

**Supporting:** systematic change and occasion/developmental effects relevant to interpreting longitudinal dependability.

**Conditional exploratory:** incremental predictive validity beyond baseline outcome, relevant covariates, and global cognition. This is not performed in Step 2C.

The five-task proxy is a feasibility specification only and is not promoted to the final measurement specification without an explicit evidence-based decision.

## Estimands and cohorts

The primary future estimand is agreement/dependability for frozen task fields across eligible cognitive occasions, with separate level and shape summaries. Change, practice, occasion/developmental effects, and measurement error must be reported as distinct concepts. The first-two-eligible cognitive-pair cohort and the ses-1-based profile/outcome cohort are separate and must not be substituted.

## Construction, missingness, and pairs

The selected profile and QC rules are read from `executable_specification.json`. Fixed task identity is required across occasions. Report at-least-one, 2+, 3+, all unordered pairs, first-two pairs, complete ses-1/ses-2 pairs, and interval summaries separately. Never count visits minus one as all pairs. Preserve overlapping flags and use the reconciled sequential flow only as a descriptive accounting order.

## Measurement and transformations

Freeze raw field meaning, denominator, conditions, units, direction, and QC scope before scoring. Accuracy-like fields may be higher-is-better and speed fields lower-is-faster only where the manifest supports that proposal. Do not assume age adjustment, norm-based standardization, learned transformations, weighting, or error correction; each requires a prespecified rationale and, where learned, leakage-safe fitting.

## Reliability/agreement and uncertainty

Reliability/dependability is primary future work. After specification freeze, report the selected agreement model, within-person variability, SEM/MDC uncertainty, interval sensitivity, and participant-level dependence. Cohort-level change cannot be treated as individual reliable change. Unknown comparability must be reported and can block a particular interpretation without blocking unrelated supplementary tasks.

## Robustness and prediction gate

Planned sensitivities include documented valid/likely-valid, strict documented V-only, unresolved-inclusive, first-two versus scheduled pairs, and full versus reduced profile. Incremental prediction is conditional exploratory and requires baseline outcome, relevant covariates, global cognition, frozen profile construction, outcome timing, and missingness policy. It does not determine task selection.

## Remaining choices and block scope

QC scope/code meaning blocks selected-score eligibility until approved; LNB/CPT denominators and ADT units block those particular interpretations; PCET/AIM/Trails placement blocks their domain interpretation but not the current proxy; Digit Symbol version blocks its update-sensitive speed interpretation; continuation handling blocks treating ses-2 as a new CNB occasion; weighting/direction/age policy block final composites and prediction. These questions do not automatically block the entire study or every supplementary task. No reporting gate is declared validated here.
