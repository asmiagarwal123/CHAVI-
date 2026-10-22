# STEP 5B-C1 — Empirical protocol and decision report

## Verdict

**EMPIRICAL PROTOCOL READY FOR EXECUTION REVIEW.** This package freezes a feasible analysis and validates its software on synthetic data. It does not calculate any empirical profile level, shape, ICC, change estimate, interval, participant report, or prediction, and it does not authorize the next run automatically.

## Research question and scope

How do observed five-task longitudinal profile agreement and change depend on reference estimation, scaling, support restrictions, and quality-control/pair selection in the selected Penn LEAD sample?

The primary analysis is the 52-person Primary V/F cohort, its two already selected occasions, the five frozen tasks in contract order, Design B, M0/MAD, and complete pairs only. The primary estimands are ICC(A,1) of profile level, mean level change, and pooled RMS centered-shape displacement. M0/SD uses the same 52 pairs. M0 versus M1 is a matched comparison on the 42 M1-supported Primary pairs. Fixed-primary-pair strict-V (41) and reselected strict-V (45) are separate descriptive cohort sensitivities; the latter changes four pair definitions (`sub-20149`, `sub-20310`, `sub-20902`, `sub-20916`) and therefore combines eligibility and occasion selection.

The 5,520 expanded transformation rows are representations, never independent observations. Reference A has 109 identities; Design B has 52 targets plus 57 auxiliaries. Frozen held-out counts are 11/11/10/10/10 and fitting counts 98/98/99/99/99. M1 complete pairs are 42/36/33 for Primary/reselected/fixed-pair cohorts; no M0 fallback can enter M1.

## Estimands and interpretation

For participant i, occasion t and five-vector z_it, `L_it = sum(z_it)/5` and `q_it = z_it - L_it 1`. Mean level change is `sum_i(L_i2-L_i1)/n`. RMS shape displacement is `sqrt(sum_i sum_j[(q_i2j-q_i1j)^2]/(5n))`; it is not the arithmetic mean of participant-specific RMS distances.

ICC(A,1) uses `(MSR-MSE)/(MSR+(k-1)MSE+k(MSC-MSE)/n)`, k=2, with df n-1, 1, and n-1 for row, occasion, and residual mean squares. Integer frequency weights are exactly row expansion after zero-weight identities are removed. Finite negative ICCs are retained. Degenerate denominators, constant data, active nonfinite values, or frequency n<2 yield an explicitly undefined result. The statistic describes between-person absolute agreement of level for this sample and these occasion columns; it does not establish the reliability or clinical meaning of an individual child's profile.

Profile correlation is retained only as a descriptive distribution, with flat/near-flat pairs reported undefined. Scatter and vector-trace association are deferred: they do not materially improve the frozen primary answer, and vector trace was not assessed by B3-R. Large RMS displacement has no clinical interpretation without an external validated threshold.

## Uncertainty decision

The default is a 95% P3 joint-refitting percentile interval for each primary endpoint, always accompanied by the P2 fixed-transformation percentile interval. P2 and P3 basic intervals are labeled sensitivity analyses. P1 is simulation-only because population reference parameters are unknown. P4 is deferred because no incremental empirical purpose justifies a fold-stratified target population. M0/MAD remains the planned coordinate definition; M0/SD changes the coordinate/estimand and is not a better interval for MAD.

This choice was informed after—not preregistered before—the completed simulations. Across repaired continuous S1 results, P3 percentile conditional coverage was 0.9425 for ICC, 0.9365 for mean change, and 0.9175 for RMS; P2 percentile values were 0.936, 0.9325, and 0.803. Basic P3 improved S1 mean-change/RMS coverage but performed worse for ICC (0.898). In discrete S5/MAD, P3 percentile availability was only 0.63 for every endpoint, despite conditional coverage of 0.9317/0.9357/0.9563; P2 availability was 0.997. Thus no method is called universally calibrated, conditional coverage is never separated from availability, and all planned alternatives—including undefined/unavailable results—are retained. The complete matrix includes both scales, both families, all primary endpoints, P1–P4, S1 and S5, MCSEs and availability.

The bounded budget is exactly 999 attempts per method, at least 950 valid draws, `floor(.025*n_valid)>=20`, linear quantiles, no redraw-until-success, no smoothing/jitter, and no adaptive method/family changes. This operational gate does not prove coverage or tail precision.

## Empirical resampling contract

Participants are paired clusters; both occasions travel together. P2 and P3 share the target multiplicity draws. P3 samples targets and auxiliaries independently within their original roles, conditioning on the observed role membership, frozen cohort, selected pairs, and fold assignment. Target analysis and reference multiplicities are identical; all copies of a held-out identity are excluded from its fold fit; one auxiliary draw is shared across folds; only represented folds are fit. Raw authorized reference records are refit using the frozen mean/OLS, MAD/SD and support formulas. Zero-weight identities are removed before reductions; missing and unsupported values are never zero; failed draws and reason codes persist without redraw.

Empirical eligibility has no truth or coverage gate. The output schemas prohibit truth/coverage fields. Intervals for the 45-, 41-, and M1-supported subsets are deferred because their reference membership, subset selection, changing n, physical-source linkage, and target populations have not been separately frozen.

## Reporting and multiplicity

Every row carries status, denominator, pair-identity hash, exclusions, support/model/scale/reference design, contract and input hashes, and uncertainty label. There is no formal hypothesis testing and no significance-based selection; multiplicity adjustment is therefore not applicable. Interval overlap is not a test of differences. Matched transformation comparisons are separated from cohort-selection comparisons. Complete cases do not justify missing-at-random or population-generalization claims.

## Measurement limits and claims

Repository session ordering is not verified elapsed time. LNB scoring denominator/load, CTAP unit/aggregation, task versions/administration, exact timing, and complete-case selection remain unresolved. These restrict interpretation but do not block the mechanically defined primary analysis. The work cannot support diagnosis, norms, causal development, latent ability, task-version equivalence, clinical thresholds, predictions, participant reports, or proven novelty. Any contribution is a provisional, dataset-bound identity-aware analysis of reference uncertainty.

## Literature basis

Cronbach and Gleser (1953; DOI 10.1037/h0057173) motivate separating profile level, pattern/shape and overall distance and warn that profile similarity depends on dimensions and units. McGraw and Wong (1996; DOI 10.1037/1082-989X.1.1.30) distinguish ICC forms and absolute agreement from consistency. Carpenter and Bithell (2000; DOI 10.1002/(SICI)1097-0258(20000515)19:9<1141::AID-SIM479>3.0.CO;2-F) show that bootstrap interval choice and implementation require explicit operating assessment. Morris, White and Crowther (2019; DOI 10.1002/sim.8086) support ADEMP separation and reporting Monte Carlo error. These are established methods; CHAVI's linked P3 implementation and application are proposals, not proven novelty.

## Executable readiness and next run

`analysis_interface.py` provides strict schema/key/support checks, frequency-weighted reference primitives, M0/M1 fitting without fallback, profile endpoints, configurable participant counts/folds, linked resampling plans, an empirical-only availability gate, deterministic seed construction, and metadata-only dry-run. `independent_synthetic_validator.py` freezes expected values through a separate explicit-expansion formula path before importing production code. It passed 27 tests covering common shifts, shape-only changes, constant profiles, negative ICC, unsupported values, zero-weight NaNs, absent folds, unequal multiplicities, zero/near-zero scales, row shuffling, duplicates, task order, occasion keys, mixed model/scale, fallback contamination, visit decoupling, held-out leakage, auxiliary linkage, and truth-gate reuse.

After separate authorization, the next run would compute three primary point estimates and P2/P3 percentile plus labeled basic intervals. At 999 attempts for each of P2 and P3, P3 entails at most 24,975 task-fold fits (999×5 folds×5 tasks) plus transformations/endpoints; P2 reuses fixed coordinates. Checkpointing is per method/replicate with hash validation and deterministic resumption. Descriptive sensitivities follow without intervals under v1. No empirical run starts here.

## Completion checklist

- PASS — Authoritative chain and repaired versions: `source_version_register.csv`, required hashes matched.
- PASS — Question, estimands, cohorts and identities: contract, registry, linkage checks.
- PASS — Cross-endpoint uncertainty and failure regimes: decision matrix and this report.
- PASS — Executable resampling/support: interface and 27-test synthetic record.
- PASS — Secondary scope, reporting and multiplicity: contract, schemas, claims register.
- PASS — Independent synthetic/corruption tests: `synthetic_test_results.json`.
- PASS — Reproduction, manifest, ZIP and preservation: README, manifests and protected-input comparison.
- PASS — No empirical outcomes generated: empty schemas and readiness verdict.
