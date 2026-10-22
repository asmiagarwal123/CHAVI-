# CHAVI Step 5B-B1 — Profile estimand, analysis, and uncertainty protocol review

**Status:** RECOMMENDED SCIENTIFIC PROTOCOL — NOT YET ADOPTED FOR EMPIRICAL EXECUTION.

## Outcome and evidence boundary

The accepted Step 5B-A contract hash and clean ZIP hash were directly recomputed and matched. The package manifest, cohort/fold identities, source/provenance keys, transformation code, historical method drafts, reviews, and handoffs were inspected. Handoff assertions are recorded as summaries unless corroborated. Historical Design-C and task-level results are context only; quarantined numerical outputs are not current Design-B results. This review generated no empirical level, scatter, shape, correlation, ICC, bootstrap interval, simulation, classification, or prediction.

The support audit reproduces M1 complete pairs (per MAD or SD): Primary 42/52, reselected strict-V 36/45, and fixed-primary-pair strict-V 33/41. M0 is complete at 52/52, 45/45, and 41/41. Unsupported M1 coordinates remain null; fallbacks are not counted. Expanded transformation rows are representations, not new observations.

## Recommended scientific question

Quantify how observed longitudinal five-task profile stability changes under sample-reference estimation, reference sharing, transformation choice, support restriction, and uncertainty propagation in this small developmental cohort. This is stronger and more feasible than an application UI, task ICCs alone, an assumed “shape is less stable” conclusion, or intervals pasted onto unvalidated methods because it makes the transformation/reference mechanism itself testable. The candidate contribution is the dataset-specific, identity-aware evaluation of cross-fitted MAD transformation uncertainty; novelty and operating performance still require simulation and comparison with existing profile methods.

Observed longitudinal stability is not pure measurement reliability. Two selected occasions with uncertain timing cannot distinguish error, development, practice, state, administration, or task-version change. Such interpretation would require known assessment timing, standardized repeated administration, short-interval replicates and/or multiple waves, version metadata, measurement-invariance evidence, and a longitudinal measurement/error model.

## Geometry and mapping

For task-ordered `z`, use `L=mean(z)`, `q=z-L1`, and `S=sqrt(||q||²/5)`. The fixed 5×4 Helmert matrix has column `k` (1–4) equal to `1/sqrt(k(k+1))` in rows 1..k, `-k/sqrt(k(k+1))` in row k+1, and zero afterward; `c=Hᵀz`. Thus `q=Hc`, `sum(q)=0`, `||q||²=||c||²`, and `||z||²=5L²+||c||²`. Historical formulas agree on denominator 5 but an earlier document incorrectly described five centered entries as five orthogonal components; this protocol records four independent contrasts.

Pair changes are `ΔL`, `ΔS`, `D_shape=sqrt(||q2-q1||²/5)`, and `D_total=sqrt(||z2-z1||²/5)`, with `D_total²=ΔL²+D_shape²`. Profile correlation is defined only above `64*eps*max(||z||,sqrt(5)|L|,tiny)` for each shape norm. This conservative floating-point rule is declared before empirical viewing; a flat/near-flat profile is unsupported. Correlation measures direction and can be high despite magnitude disagreement. Unit-scatter normalization is not default because it changes the estimand.

## Estimand recommendation and comparisons

The small primary set is level ICC(A,1), mean level change, and RMS absolute shape displacement. Shape trace association is a secondary descriptive candidate pending simulation; it is a Frobenius/cosine association of centered 4D person-by-contrast matrices, invariant to a common orthonormal contrast rotation, but is neither an ICC nor classical true-score reliability. Scatter ICC(A,1), participant profile-correlation distribution, and matched-cohort task ICC(A,1)s are secondary/descriptive. ICC(C,1) for level may be reported descriptively to expose consistency versus agreement, never as an interchangeable primary.

Primary is Primary V/F–M0–MAD. M0/SD uses the same pairs. M0 versus M1 uses identical M1-supported pairs, with full-cohort M0 separately labelled. Fixed-primary-pair strict-V isolates QC on fixed occasions; reselected strict-V changes occasion selection. Cross-sectional age residualization is not a developmental trajectory model. Historical task ICCs with other denominators are context, not matched baselines.

## Readiness and unresolved adoption

Geometry, code paths, support rules, identity-linked bootstrap pseudocode, schemas, and synthetic checks are decision-ready. Empirical execution, interval family, the secondary trace statistic, and joint-bootstrap design require researcher adoption. Coverage and failure behavior require the specified ADEMP study. Reference alternatives—auxiliary-only common fitting, leave-one-target-out, and fold sensitivity—are future diagnostics, not assumed improvements.

## Consolidated recommended project scope

CHAVI should study observed longitudinal level and four-dimensional relative-shape behavior of five explicitly named task measures in Penn LEAD `ds007116` v1.0.6, bounded to the audited 52-person Primary cohort and its declared strict-V and M1-support sensitivities; its proposed methodological contribution is an identity-aware assessment of how cross-fitted internal reference estimation, shared parameters, robust scaling, and support rules affect profile-stability summaries, evaluated by independent synthetic verification and a preregistered ADEMP known-truth simulation before empirical intervals or method claims; it must not interpret the five tasks as validated latent domains, the level as general intelligence, observed changes as decomposed development or measurement error, or any output as diagnostic, clinical, predictive, individually reportable, or proof of reliability.
