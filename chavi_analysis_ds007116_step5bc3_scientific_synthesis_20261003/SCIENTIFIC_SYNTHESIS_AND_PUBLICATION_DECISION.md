# Scientific synthesis and publication decision

## Executive assessment

The strongest supported contribution is a **failure-aware evaluation of uncertainty from an estimated reference transformation in longitudinal five-task profiles**, paired with a reproducible empirical sensitivity illustration. It is simultaneously methodological and reproducibility-oriented; the empirical component is descriptive rather than clinical or causal. The work is differentiated by the linked combination of cross-fitted reference scaling, level/shape estimands, fixed-versus-refitted bootstrap comparison, and joint reporting of coverage, availability, available-and-covered probability, width, failure reasons, and Monte Carlo error. Targeted searching found prior work on every component, but did not find this exact combination; that means “not found in this search,” not “does not exist.”

**Recommendation: proceed to a bounded manuscript draft now.** Resolve the measurement metadata listed below before submission or narrow the language accordingly. No additional generic audit or unapproved experiment is warranted.

## Authoritative evidence chain

The package uses the 5B-A clean rebuild and transformation contract, 5B-B1 definitions, 5B-B3-R repaired results (which supersede affected B3 values), 5B-C1 frozen protocol, and 5B-C2 machine tables/validation. The expected C2 ZIP, C1 contract, and B3-R ZIP SHA-256 values were checked once against the available signed sidecars/manifests: `5d5d4f…a32fa`, `0bd5b1…e6703a`, and `b4c781…5398b`. Detailed locators and full hashes are in `input_manifest.csv`.

## Implemented estimands and units

Task order is exactly letter n-back, face memory, matrix reasoning, emotion recognition, dominant finger tapping; all directions are +1. For reference observations in the applicable training fold,

`z_ijt = (y_ijt - arithmetic_mean(reference training y_j)) / s_j`,

where primary `s_j = median(|y_j - median(y_j)|) / 0.6744897501960817`; SD sensitivity uses sample SD with `ddof=1`. Units are reference-scaled score units. Design B assigns 52 targets to five held-out folds of 11/11/10/10/10 and fits on 98/98/99/99/99 reference participants: the target's own reference record is excluded from its fold fit while auxiliaries remain.

For participant `i`, occasion `t`, and five tasks (`J=5`):

`L_it = (1/5) Σ_j z_ijt`, `q_ijt = z_ijt - L_it`.

The occasion order is occasion 2 minus occasion 1. Mean level change is `n^-1 Σ_i (L_i2-L_i1)`. Pooled RMS centered-shape displacement is

`sqrt[(1/(5n)) Σ_i Σ_j (q_ij2-q_ij1)^2]`.

It is not the mean of participant-level RMS values. ICC absolute agreement, single measurement is implemented with `k=2` and degrees of freedom `(n-1, 1, n-1)`:

`ICC(A,1) = (MSR-MSE) / [MSR+(k-1)MSE+k(MSC-MSE)/n]`.

Participant profile correlation is Pearson correlation of the two centered five-coordinate profiles subject to the frozen degeneracy rule; it removes level and relative scatter and is descriptive only.

## Empirical evidence

All 18 planned point estimates appear in `aggregate_tables/empirical_all_planned_point_estimates.csv`. The primary 52-pair M0/MAD estimates are ICC 0.618912, mean level change 0.365668, and RMS shape displacement 1.001646. All 12 primary intervals are in `aggregate_tables/empirical_primary_intervals.csv`; each method/endpoint had 999/999 valid draws.

For percentile intervals, P2 versus P3 widths were 0.412591 versus 0.406597 for ICC (difference −0.005994; ratio 0.9855), 0.374731 versus 0.368696 for mean change (−0.006036; 0.9839), and 0.387236 versus 0.570940 for RMS displacement (+0.183704; 1.4744). Basic widths are identical within each method/endpoint because the stored basic construction reflects the same bootstrap quantile span. These are descriptive realized-interval comparisons—not tests of superiority and not isolated reference-variance estimates.

The primary profile correlations were defined for all 52 pairs: minimum −0.6894, Q1 0.1210, median 0.5489, Q3 0.8744, maximum 1.0000. This broad distribution does not establish individual-profile reliability.

Sensitivity estimates must remain separate. M0/SD (`n=52`) yielded 0.599329, 0.307894, 0.856714. On matched M1-supported identities (`n=42`), M0/MAD yielded 0.602117, 0.386952, 1.054075 and M1/MAD yielded 0.605198, 0.105448, 1.107180. Fixed strict-V (`n=41`) yielded 0.664594, 0.260585, 0.819450; reselected strict-V (`n=45`) yielded 0.674547, 0.281061, 0.839648. Values are ordered ICC, mean change, RMS displacement. M0–M1 differences are not causal age effects, and differences across denominators do not isolate a method effect.

Cohort flow is 109 reference-A participants, 52 primary pairs, 42 matched-support pairs, 41 fixed strict-V pairs, and 45 reselected strict-V pairs. Counts were derived from authoritative identity manifests/reconciliation rather than treating an “exclusions” filename as exhaustive. No identities are published.

## Simulation evidence

The corrected pilot has 100 outer replicates in six scenarios: S1 continuous correlated level/shape; S2 correlated level but zero cross-occasion shape correlation; S3 S1 plus common +0.5 shift; S4 S1 plus a +0.5 first-Helmert shape shift; S5 S1 followed by nearest-integer, ties-to-even rounding; and S6 independent per-task/occasion 0.6 point mass at the task mean (making MAD structurally undefined) with deviations retained at probability 0.4. The confirmatory evaluation has 2,000 outer replicates only for S1 and S5. Therefore S2–S4/S6 findings are pilot evidence.

`simulation_synthesis_all_prespecified.csv` contains all 384 prespecified stage/scenario/scale/endpoint/method/family cells. Conditional coverage divides covered available intervals by available intervals. Availability divides available intervals by attempted outer replicates. Available-and-covered divides covered available intervals by all attempted outer replicates. Width is summarized among available intervals. `simulation_failure_reason_summary.csv` aggregates stored resample status reasons, and `simulation_paired_monte_carlo_comparisons.csv` preserves paired method differences and their stored MCSEs.

The required anchors reconcile exactly. In S1/MAD RMS percentile results, P2 covered 1,606/2,000 (0.803) and P3 covered 1,835/2,000 (0.9175); both were fully available. P3 is better in this comparison but still below nominal 0.95. In S5/MAD RMS percentile results, P2 availability was 1,994/2,000 and available-and-covered was 0.916; P3 availability was 1,260/2,000 and available-and-covered was 0.6025. P3 conditional coverage was 0.95635 among available intervals, but that figure cannot be interpreted without its 37% unavailability. Neither method is universally calibrated or superior.

S1 plausibly probes smooth continuous scores; S5 plausibly probes bounded integer/tied scoring. S6 diagnoses extreme robust-scale degeneracy. Yet the empirical mixture of integer totals, true-positive counts, and a tapping mean does not prove that Penn LEAD is generated by S1, S5, or S6. Valid empirical bootstrap draws do not resolve simulation undercoverage.

## Literature positioning and novelty boundary

Cronbach and Gleser established profile elevation/scatter/shape distinctions; McGraw and Wong established ICC forms; Carpenter and Bithell reviewed bootstrap interval behavior; Chernozhukov et al. established cross-fitting for nuisance estimation; Morris, White, and Crowther established ADEMP and Monte Carlo reporting principles. These are reused foundations, not inventions here. Penn CNB and broader longitudinal neurocognitive studies show that repeat testing can affect change interpretations. The Penn LEAD descriptor is a 2025 **preprint**, not peer-reviewed as of the search date, and describes 132 adolescents/225 imaging sessions; its raw-accession wording differs from the local ds007116 derivative/repository label, so accession equivalence is not silently assumed.

Candidate original contribution: the prespecified, repaired, failure-aware comparison of freezing versus jointly refitting this cross-fitted five-task reference transformation, linked to all three profile endpoints and a fully validated empirical execution. Exact evidence and nearest work are in `closest_work_matrix.csv`. Novelty remains bounded because the search was targeted, not systematic.

## Claim classes

- **A—established methods:** robust/reference scaling, profile centering, ICC(A,1), participant bootstrap, joint refitting, cross-fitting, ADEMP/MCSE.
- **B—project-supported findings:** all empirical estimates, interval endpoints, repaired simulation performance, failure counts, and cohort counts.
- **C—literature-supported findings:** practice effects can complicate repeated cognitive assessment; profile correlation differs from agreement; bootstrap behavior depends on estimator/data regularity.
- **D—candidate contribution:** failure-aware end-to-end evaluation of estimated-reference uncertainty for these longitudinal profile summaries, plus auditable reproduction.
- **E—untested:** real-data membership in a simulated mechanism; measurement equivalence; causal age/development/practice decomposition; clinical meaning; generality beyond this design.

## Measurement and validity limitations

| Issue | Documented | Unresolved / threatened interpretation | Response |
|---|---|---|---|
| Task-version comparability | Matching score fields and session labels | Equivalent difficulty/measurement across versions or occasions | Narrow wording; seek curator documentation |
| Session timing | Session IDs were assigned chronologically from repository/Flywheel timestamps; acquisition times are rounded | Precise elapsed time and developmental rate | Use occasion order only; additional documentation |
| LNB | `cnb_lnb_mcr` is true-positive responses for 1- and 2-back trials | Denominator and load composition | Field-specific wording; obtain instrument metadata |
| CTAP | `cnb_ctap_dom` is mean of dominant-hand trials | Unit and exact aggregation | Do not label taps/second; obtain metadata |
| Complete-case selection | Cohorts require available/eligible task pairs | Selection/generalizability beyond analyzed pairs | Report denominators; no population claim |
| Practice effects | External literature documents retest effects | Their magnitude here and separation from development | No causal change attribution; future design if scientifically required |
| Reference composition | Reference A and fold structure are frozen | Normative-population representativeness | Say reference-scaled, not normed |
| Support restrictions | M1 and strict-V analyses change support/eligibility | Isolated model effect across differing samples | Keep matched/fixed/reselected analyses separate |

The level-change unit is the implemented transformed unit. RMS includes measurement variability. A positive interval for a nonnegative displacement is not itself proof of genuine individual change. Profile correlation is not reliability evidence.

## Remaining research decision

No new simulation is required to support the narrow manuscript. If reviewers demand a claim of general calibration across realistic Penn LEAD scoring mechanisms, present evidence is insufficient. The minimal future experiment would specify empirical-marginal mixed mechanisms for all five tasks, including documented bounds/ties and reference composition, then prespecify P2/P3 coverage, availability, available-and-covered, width, and failure criteria over enough outer replicates to keep MCSE acceptably small. Success would require prespecified near-nominal coverage **and** high availability across endpoints; failure would remove general-calibration language. Cost is moderate-to-high compute plus essential measurement metadata. This experiment is not executed here.

