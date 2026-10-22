# CHAVI Step 3B statistical analysis plan draft

**Status:** `PROPOSED—NOT APPROVED`. This document prepares analysis decisions after Step 3A and before statistical inference. It is not a frozen SAP, preregistration, reliability result, prediction result, or reporting-engine decision. The five fields remain narrow task measurements and a provisional fixed-task profile; they are not validated broad-domain measures.

## 1. Scope, estimands, and analysis order

CHAVI asks whether selected non-diagnostic cognitive measurements and their relative pattern are dependable across the observed longitudinal occasions, separating overall profile level from relative profile shape and reporting uncertainty. The primary population is the eligible Penn LEAD participant cohort under an explicitly named QC policy and pair rule. The long, variable intervals mean that observed change can combine measurement variation, development, practice, and context; it is not automatically measurement error.

The minimum defensible order is:

1. descriptive retention, missingness, score distributions, floor/ceiling checks, age support and nominal interval checks;
2. raw task-score longitudinal agreement and systematic change;
3. frozen-reference profile level and centered-shape analyses, only if score definitions, directions, units and comparability are approved;
4. robustness analyses on common participants and policy-specific cohorts;
5. conditional exploratory prediction, only after the measurement specification and outcome timing are frozen.

Every inferential output must identify the estimand, task/field, QC policy, pair rule, cohort, transformation/reference, sample size, uncertainty method, assumptions, failures and specification hash.

## 2. Candidate measurements and cohorts

The provisional five-task candidate is:

| Narrow task | Exact field | Provisional raw interpretation | Main unresolved issue |
|---|---|---|---|
| Letter n-back | `cnb_lnb_mcr` | Released true-positive summary | denominator/load mapping and version |
| Face memory | `cnb_cpf_cr` | Released correct-count score | false-alarm treatment and version |
| Matrix reasoning | `cnb_pmat_cr` | Released correct-count score | stopping rule and version |
| Emotion recognition | `cnb_er40_cr` | Released correct-count score | historical version/condition pooling |
| Dominant-hand finger tapping | `cnb_ctap_dom` | Released dominant-hand summary | count/rate aggregation and hand definition |

The executable Step 3A policy is the sole source for current provisional eligibility. The recommended candidate policy accepts exact-dictionary `Valid` and documented `Likely valid` only when all applicable QC fields are present. Strict `Valid`-only and unresolved-inclusive policies are sensitivities. Missing, partial, no-QC, unknown, skipped and invalid states remain distinct. No imputation is proposed.

The primary pairing recommendation is the first two eligible occasions per participant, **PROPOSED—NOT APPROVED**, because it gives one simple participant-level pair while respecting task eligibility. The complete scheduled `ses-1`/`ses-2` rule is a **PROPOSED—NOT APPROVED** sensitivity. All unordered pairs are descriptive or used only in a grouped model/resampling analysis; they are not independent participants. The scheduled outcome cohort is separate from the first-two repeated cognitive cohort.

The prepared profile manifest requires the same five exact task/field identities at both occasions. Same-domain substitution is not allowed. A reduced four-task profile may be a separately named sensitivity, not an interchangeable replacement.

## 3. Raw task-score longitudinal agreement

**Question and estimand.** For each exact released task score, what is the population-level single-measure absolute agreement across the selected pair rule and observed interval mixture? A paired difference is a longitudinal change descriptor, not pure measurement error.

**Inputs.** `paired_task_observations.csv`, one task at a time, with participant as the dependence unit; primary candidate policy and first-two pair rule after approval; strict and scheduled alternatives.

**Proposed analysis.** Report raw-unit paired values, mean and median change, SD/IQR of change, interval distribution, difference-versus-average plots, and an absolute-agreement ICC only after its convention is numerically verified. Do not convert `cnb_lnb_mcr` to a percentage or infer denominators. Do not combine counts, times and rates on the raw scale.

**Uncertainty and failure.** Use participant-cluster bootstrap or another prespecified participant-level interval method; record degenerate/failed resamples. Report negative or undefined estimates unchanged. Zero variance, unresolved score meaning, nonpositive timing or unsupported comparability blocks the corresponding interpretation rather than causing automatic repair.

**Sensitivity.** Recommended versus strict QC; first-two versus scheduled pairs; raw task score versus an approved reference-aligned sensitivity; common-participant comparisons; and exclusion of a task only when its definition is independently blocked. These are **PROPOSED—NOT APPROVED**.

## 4. Direction, transformation, and reference scale

Accuracy-like fields are tentatively higher-is-better. Speed fields, if approved, are tentatively lower-is-faster and would be direction-reversed before a profile mean. These are **PROPOSED—NOT APPROVED** and require task-specific review. Finger tapping is a released motor-speed summary; its direction is not proof of a general ability.

The minimum defensible profile-scale choice is a task-specific study-reference z-score using one frozen reference mean and SD for both visits:

`z_itd = (direction_aligned raw score_itd − reference mean_d) / reference SD_d`.

This is a numerical study reference, not a population norm or clinical percentile. A zero reference SD, unsupported unit conversion, unresolved denominator, or score-definition conflict makes that component unavailable for the profile analysis. The raw-score analysis remains the transparent primary measurement record.

For descriptive profiling, a baseline reference fitted without outcome information is **PROPOSED—NOT APPROVED**. For prediction, every learned reference, direction choice, imputation decision (none currently proposed), or scaling step must be fitted within the training participants. Separately standardizing each visit is not recommended because it can remove systematic occasion differences relevant to absolute agreement.

Equal weighting of the five available standardized task scores is the minimal transparent level convention, **PROPOSED—NOT APPROVED**. It does not imply equal latent importance or a validated global cognition construct. Learned weights are not proposed for the primary analysis because optimizing them on the same data would make dependability appear independent when it is not.

## 5. Profile level and centered profile shape

If the five components are approved on a common reference scale, define:

`L_it = mean_d(z_itd)`

`S_itd = z_itd − L_it`.

`L` is the overall level of the selected-task profile; `S` is relative shape. Neither should be called intelligence, global cognition, or a validated domain profile.

The direct level-versus-shape comparison must use the same participant and pair cohort, same reference and same task identities. Report level agreement and change separately from each centered component and a prespecified shape-discrepancy summary. A minimal discrepancy is:

`D_shape_i = sqrt(mean_d((S_i2d − S_i1d)^2))`.

Shape correlation is supplementary only: five components provide a short vector, correlation is undefined for a flat profile, and it misses amplitude changes. Flat profiles therefore receive `shape_correlation_status=not_estimable`; their level and discrepancy can still be described if all five components are valid. Four prespecified orthonormal contrasts are the minimal identifiable shape representation for any later regression; all five centered components plus an intercept are linearly dependent.

Because centering shares the estimated level across components, uncertainty must be joint/participant-level. Independent component intervals are not sufficient. No shape score is computed in Step 3B.

## 6. Age, interval, and extrapolation

Raw-score agreement and age-relative agreement answer different questions. The primary descriptive display should use session age and nominal elapsed interval without fitting an age effect. A restrained age-adjusted sensitivity, **PROPOSED—NOT APPROVED**, may use a prespecified linear score-on-age reference only if the observed age support is adequate and the model is scientifically justified before looking at agreement results.

The mixed age reference must not be described as an individual developmental trajectory. Baseline age cannot replace follow-up age. A fitted age curve outside the observed support is extrapolation and must be flagged or blocked. Current rounded/anonymized acquisition times do not establish exact cognitive-assessment dates. Age, elapsed time and visit order are related; including all without a clear estimand risks collinearity.

## 7. ICC(A,1), consistency comparison, and convention

**Scientific question.** ICC(A,1) targets single-measure absolute agreement: occasion-wide shifts count against agreement. A consistency ICC is a different estimand and may be a sensitivity, not a substitute.

**PROPOSED—NOT APPROVED computational convention.** For a complete two-occasion paired sample, implement and independently hand-check the two-way model matching the chosen absolute-agreement definition, including the exact fixed/random occasion convention. Verify the implementation against synthetic data with known occasion shifts, perfect agreement, constant scores, and negative estimates. Do not rely on the label `ICC(A,1)` without recording the formula, software/version, denominator and missingness rule.

Report the estimate, CI method, participant count, occasion/pair rule, interval distribution, mean occasion difference, variance components or dispersion, and convergence/degeneracy status. A consistency ICC or Pearson correlation may be shown as a clearly labelled sensitivity because perfect ordering can coexist with systematic shift; neither establishes construct validity.

## 8. Participant-level bootstrap and preprocessing uncertainty

Resample participants with replacement, carrying all eligible observations and pair rows for each sampled participant together. Do not resample pair rows independently. A fixed-reference bootstrap estimates conditional uncertainty; refitting a data-estimated reference, age adjustment or weighting inside each resample estimates more of the full-pipeline uncertainty. The target must be named.

**PROPOSED—NOT APPROVED.** Use a fixed seed and several thousand participant resamples where computationally feasible, record failed/degenerate samples and assess endpoint stability. Refit any learned preprocessing inside the resample when it is part of the estimand. Do not interpret a cohort CI as an individual child’s reliability interval or a personalized error guarantee.

## 9. Systematic change and parsimonious mixed model

Report paired change and change-versus-average plots before model interpretation. A minimal mixed model for repeated raw scores is:

`score_it = beta0 + beta1 * baseline_age_i + beta2 * elapsed_time_it + b_i + error_it`.

Here `b_i` is a participant random intercept. This is **PROPOSED—NOT APPROVED** and should be fit only after checking support, missingness, convergence and collinearity. It describes association with age/time; it does not separate development from practice or identify pure measurement error. Random slopes and complex variance structures are not minimal choices for this sample and visit density.

Report fixed-effect estimates with uncertainty, participant and observation counts, residual diagnostics, singular/convergence status and the exact time definition. If the model is not estimable or is sensitive to reasonable alternatives, retain descriptive change only.

## 10. SEM/MDC interpretation limits

The familiar formulas `SEM = SD * sqrt(1 − reliability)` and `MDC95 = 1.96 * sqrt(2) * SEM` are conditional on a suitable reliability and error model. They should not be presented as clinical thresholds, meaningful-change thresholds, or individualized guarantees. With unequal or correlated occasion errors, the difference-error variance must be used instead.

**PROPOSED—NOT APPROVED.** Report SEM/MDC only as conditional statistical quantities for a frozen score, scale, pair interval and agreement model, with the assumptions and units displayed. Suppress or label `not interpretable for pure measurement error` when long-interval change, systematic bias, uncertain task equivalence, or an unresolved score definition makes those assumptions untenable. No SEM/MDC estimates are run in Step 3B.

## 11. Missingness, attrition, common cohorts, and multiplicity

Preserve absent row, absent value, documented skip, invalid score, unresolved QC, unparseable value, and uncertain timing as separate states. Do not mean-impute cognitive measurements. Task-level analyses use their own eligible repeated cohorts; direct level-versus-shape comparisons use the same complete-profile participants. Prediction uses the separate ses-1 baseline/outcome intersection.

Describe retained versus excluded participant counts and available baseline age/recruitment/context variables without turning recruitment or diagnosis into a CHAVI target. Small subgroup comparisons are descriptive and uncertainty-qualified. Compare policy results on common participants as well as policy-specific cohorts so apparent stability is not confused with selection.

Multiplicity is **PROPOSED—NOT APPROVED**: designate one primary task/pair estimand and one primary profile-level/shape comparison after scientific review; label other tasks, policies, outcomes and transformations secondary or exploratory. Avoid a single omnibus significance claim across five tasks and five outcomes. Report estimates and intervals for all prespecified analyses, including unfavorable or non-estimable results.

## 12. Precision and simulation checks

Before interpreting estimates, run known-truth simulations that mimic the available participant counts, two/three-visit structure, interval mixture, missingness and plausible variance/occasion-shift settings. Check recovery, CI coverage under the simulated data-generating conditions, failure rates, negative/zero-variance behavior, bootstrap endpoint stability, mixed-model convergence and shape-correlation undefined cases.

**PROPOSED—NOT APPROVED.** Use design-based simulation scenarios spanning low/moderate/high between-person variance, systematic occasion shift, within-person error, missingness mechanisms and profile-shape change. These simulations quantify what the design can resolve; they are not post-hoc power claims and do not establish real-world validity.

## 13. Conditional prediction sequence

Prediction is conditional exploratory and is not performed in Step 3B. The candidate cohort uses ses-1 baseline and the earliest subsequent observed outcome under a clearly labelled, not-approved rule; all later outcomes remain in the long table.

The minimal sequence, **PROPOSED—NOT APPROVED**, is:

| Model | Inputs | Estimand |
|---|---|---|
| P0 | training-sample outcome mean; baseline persistence comparator only when scales/interpretation permit | simple forecast benchmark |
| P1 | baseline outcome plus minimal prespecified covariates | outcome history contribution |
| P2 | P1 plus profile level | added value of overall task-profile level |
| P3 | P2 plus four fixed shape contrasts | added value of identifiable relative shape |

Primary candidate metric is held-out MAE in outcome units, supplemented by RMSE, out-of-fold R², paired loss differences and observed-versus-predicted displays. OLS is a transparent comparator; Ridge is a restrained candidate if shrinkage is needed. Model choice, tuning, scaling, reference fitting, contrast construction and covariate preprocessing must be training-only.

## 14. Participant-separated validation and preprocessing

All visits from one participant must remain in the same validation fold. An outer participant-separated design with an inner training-only tuning loop is **PROPOSED—NOT APPROVED**; final fold feasibility must be checked against the actual candidate N and missingness. If the design is too small or unstable, report a descriptive holdout or do not claim predictive evaluation.

No outcome-driven task selection, shape weighting, threshold selection or preprocessing may use outer evaluation observations. Cross-validation is internal validation, not external transport validation. Fold-level uncertainty is substantial; fold SD divided by the square root of the number of folds is not automatically a generalization interval.

## 15. Measurement evidence versus predictive utility

Report two separate statuses:

- **Measurement:** task-score agreement, profile-level/shape dependability, systematic change, missingness, timing, comparability and uncertainty.
- **Predictive utility:** whether profile level or shape improves held-out outcome loss beyond baseline outcome/covariates.

A measurement result does not prove predictive utility, and a predictive association does not validate a task measurement or imply causality, diagnosis, educational benefit or clinical usefulness. A prediction model must not determine the primary task definition after seeing outcomes.

## 16. Future reporting criteria and evaluation

The future report/caution/refuse demonstrator must use claim-specific, versioned rules. A minimal structure is: block a claim when score identity, essential units, QC applicability or cross-occasion meaning is inadequate; otherwise evaluate cohort evidence and precision; then classify the research claim as supported, cautionary or withheld according to prespecified tolerances.

Any reliability lower-bound, interval-width, minimum-effective-sample or acceptable-coverage threshold is **PROPOSED—NOT APPROVED** and must be justified by the intended research claim, precision simulations and scientific review. There is no universal reliability cutoff, clinical threshold or personalized error guarantee for CHAVI. Gate evaluation must report coverage, caution/refusal rates, reason-specific counts, instability and error-versus-coverage behavior. A policy that withholds everything has zero reported coverage and cannot be described as a useful system.

Synthetic known-truth cases should test rule logic and failure handling. If an empirical error target is claimed, evaluate it on held-out participants or independent validation data; do not calibrate and evaluate the same gate on the same evidence. The Evidence Engine remains future work and is not implemented here.

## Evidence and authority

Local implementation status is governed by the Step 3A artifacts and executable specification. Method references retained from the project record are the Penn CNB official task documentation ([Explore Tests](https://webcnp.med.upenn.edu/explore-tests.html), [manual](https://webcnp.med.upenn.edu/manual.html)), Gur et al. ([CNB methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC2832711/)), Moore et al. ([CNB factor evidence](https://pmc.ncbi.nlm.nih.gov/articles/PMC4345134/)), Koo and Li ([ICC selection/reporting](https://pubmed.ncbi.nlm.nih.gov/27330520/)), Bland and Altman ([agreement](https://pubmed.ncbi.nlm.nih.gov/2868172/)), scikit-learn ([cross-validation pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)), statsmodels ([mixed models](https://www.statsmodels.org/stable/mixed_linear.html)), and Varoquaux ([small-sample validation uncertainty](https://arxiv.org/abs/1706.07581)). These support method choices and limitations; none approves CHAVI’s final specification or supplies estimates for this dataset.

## Explicit non-actions in Step 3B

No standardized scores, composites, fitted age effects, ICCs, SEM/MDC estimates, predictive models, imputation, diagnostic classification, imaging analysis, new-game analysis, additional dataset, or Evidence Engine decision is performed.
