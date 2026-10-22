# Failure aware resampling evaluation for cross fitted reference scaled longitudinal profiles

## Abstract

### Background

Longitudinal multivariate profiles are often transformed against an estimated reference sample, but a routine participant bootstrap may hold that transformation fixed. The implications for interval performance and failed resamples are rarely reported together.

### Methods

We evaluated two-occasion five-field profiles using a cross-fitted reference transformation. Prespecified endpoints were level ICC(A,1), mean level change, and pooled RMS centered-shape displacement. Repaired simulations compared oracle conditional (P1), fixed-transformation (P2), joint unstratified refitting (P3), and fold-stratified refitting (P4) procedures under MAD/SD scales and percentile/basic intervals. The six-scenario pilot was exploratory (100 outer replicates per scenario); continuous S1 and rounded/tied S5 were confirmatory (2,000 outer replicates). We jointly report conditional coverage, availability, available-and-covered probability, interval width, failure reasons, and stored paired Monte Carlo uncertainty. Frozen Penn LEAD/ds007116 results provide an empirical sensitivity illustration.

### Results

For confirmatory S1 MAD-scale RMS percentile intervals, P2 coverage was 0.803 (1,606/2,000) and P3 coverage was 0.9175 (1,835/2,000); both were fully available, and P3 remained below 0.95. For S5, P2 availability was 0.997 and available-and-covered probability 0.916, whereas P3 availability was 0.630 and available-and-covered probability 0.6025. In the primary 52-pair empirical analysis, ICC(A,1) was 0.619, mean level change was 0.366 reference-scaled units, and RMS centered-shape displacement was 1.002 reference-scaled units. The P3 percentile RMS interval was 47.4% wider than P2, descriptively.

### Conclusions

The simulations compare complete resampling procedures, not an isolated reference-uncertainty component. Joint refitting can change interval performance, but neither procedure showed universal nominal calibration and joint refitting can have substantial unavailability with tied/rounded data. Failure-aware reporting should therefore retain both coverage and availability. The empirical analysis is a worked sensitivity illustration; it does not establish causal development, task-version equivalence, individual-profile reliability, diagnosis, or normative population inference.

## Introduction

Repeated multidomain cognitive scores are frequently summarized as a single mean or as a correlation, even when their raw units differ and their interpretation depends on a reference population. Profile methods distinguish an overall elevation or level from the relative pattern among fields (shape), a distinction associated with the classic profile-similarity framework of Cronbach and Gleser. ICC forms distinguish absolute agreement from association, and bootstrap intervals offer a flexible route to uncertainty quantification. These are established methods, not inventions of the present work.

An additional issue arises when raw fields are transformed with means and scales estimated from a reference sample. Resampling target participants while freezing the fitted transform treats reference estimation as fixed. Resampling identities and refitting the transform includes more of the implemented workflow, but may encounter unsupported fits or robust-scale degeneracy. Cross-fitting is an established way of separating a target from its own nuisance fit; it does not itself establish calibration for any particular bootstrap and estimand combination.

This study asks a narrow question: for longitudinal five-field profiles transformed using a cross-fitted reference sample, how do a fixed-transformation bootstrap and a jointly refitted bootstrap differ in coverage, availability, available-and-covered probability, and width under prespecified mechanisms? We then show the frozen empirical estimates for a Penn LEAD worked illustration. The contribution is an end-to-end, repaired, failure-aware evaluation, not a claim that any one method is universally superior or that the observed empirical changes are developmental.

## Methods

### Dataset, score fields, and cohort flow

Penn LEAD is described in the peer-reviewed Scientific Data descriptor as a longitudinal clinical, cognitive, and multimodal neuroimaging resource with 132 participants and 225 imaging sessions (Sevchik et al., 2026). CHAVI analyzed the local ds007116 release and only public aggregates are reported here. The descriptor’s accession wording is not silently equated with the local frozen release.

The five fields, all oriented so that a numerically larger stored score is treated as better, were: letter n-back true positives for 1- and 2-back trials (`cnb_lnb_mcr`); face-memory total correct (`cnb_cpf_cr`); matrix-reasoning total correct (`cnb_pmat_cr`); emotion-recognition total correct (`cnb_er40_cr`); and the mean of dominant-hand finger-tapping trials (`cnb_ctap_dom`). The local metadata and external data dictionary support these field descriptions. They do not document an LNB occasion-specific denominator/load composition, the CTAP physical unit or exact aggregation, or task-version/scoring-rule equivalence. We therefore use field-specific labels and occasion-based language throughout.

Reference A contained 109 participants. The primary analysis contained 52 earlier-later paired participants. Matched M1 support had 42 pairs, fixed strict-V had 41, and reselected strict-V had 45. These are distinct analysis roles, not a sequential participant flow intended to identify causal exclusion effects. Data-quality and pair policies were frozen before C2 execution.

### Reference transformation and profile estimands

The fixed task order was letter n-back, face memory, matrix reasoning, emotion recognition, and dominant finger tapping. For task `j`, score `y`, and the relevant reference training observations, the M0 transform was:

`z = (y - mean(reference training scores)) / s_j`.

For the primary MAD scale, `s_j = median(|y - median(y)|) / 0.6744897501960817`; the SD sensitivity used sample SD (`ddof=1`). These values are reference-scaled score units, not normative clinical units. Design B placed the 52 targets in five held-out folds of 11/11/10/10/10 targets and fit the reference transform using 98/98/99/99/99 eligible reference participants. A target’s own reference record was excluded from its fold fit while auxiliary reference participants were retained.

For participant `i`, occasion `t`, and five task coordinates, level was `L_it = sum_j(z_ijt)/5`; centered shape was `q_ijt = z_ijt - L_it`. Mean level change was `mean_i(L_i2 - L_i1)`. The RMS shape endpoint was the pooled quantity `sqrt[sum_i sum_j(q_ij2-q_ij1)^2/(5n)]`, not the mean of individual RMS values. ICC(A,1), with `k=2`, was `(MSR-MSE)/(MSR+(k-1)MSE+k(MSC-MSE)/n)`. The profile-correlation summary is the correlation between each participant’s two centered five-coordinate profiles subject to the frozen degeneracy rule; it is descriptive and is not an individual-reliability estimate.

### Simulation design and performance measures

P1 conditions on the oracle transform. P2 resamples participant pairs while retaining the fitted transform and coordinates. P3 jointly resamples identities and refits the transform. P4 jointly refits while respecting the original fold structure. Percentile and basic 95% intervals were evaluated with MAD and SD scales.

The repaired pilot used 100 outer replicates per scenario. S1 was continuous with 0.8 level and shape cross-occasion correlations; S2 set shape correlation to zero; S3 added a common +0.5 shift; S4 added a +0.5 first-Helmert shape shift; S5 rounded continuous values to nearest integer with ties-to-even; and S6 independently placed 60% probability at each task mean, producing structurally undefined MAD. The S1/S5 confirmatory evaluation used 2,000 outer replicates; no confirmatory claim is made for S2–S4/S6.

Conditional coverage is covered available intervals divided by available intervals. Availability is available intervals divided by attempted outer replicates. Available-and-covered is covered available intervals divided by attempted outer replicates. Width is summarized among available intervals. These denominators are intentionally distinct. Stored paired comparisons quantify P2 minus P3 differences and Monte Carlo SEs; they are not post hoc significance tests.

### Empirical intervals, reproducibility, and ethics

The primary analysis uses P2 and P3, 999 bootstrap draws per endpoint/method, and linear quantiles for 95% percentile/basic intervals. Each of the 12 primary cells had 999 valid and zero invalid draws. C2 public aggregates were independently validated against execution outputs; B3-R supersedes affected B3 simulation results. The manuscript package contains no participant identifiers or participant-linked records. Data/code availability is limited to the released ds007116 resource, the described upstream artifacts available in this workspace, and this package; no new public repository or DOI is asserted. This secondary aggregate analysis reports no new contact with participants and should be reviewed under the applicable data-use and institutional policies before submission.

## Results

### Primary empirical analysis and all planned point estimates

Table 1 gives all 18 planned point estimates. In the primary M0/MAD, 52-pair analysis, ICC(A,1) was 0.618912, mean level change was 0.365668, and RMS centered-shape displacement was 1.001646. The centered-profile correlation was defined for all 52 pairs; its minimum, Q1, median, Q3, and maximum were -0.6894, 0.1210, 0.5489, 0.8744, and 1.0000. This wide descriptive distribution is not evidence of individual-profile reliability.

| Analysis role | n | Model / scale | ICC(A,1) | Mean level change | RMS shape displacement |
|---|---:|---|---:|---:|---:|
| Primary | 52 | M0 / MAD | 0.618912 | 0.365668 | 1.001646 |
| Scale sensitivity | 52 | M0 / SD | 0.599329 | 0.307894 | 0.856714 |
| Matched support | 42 | M0 / MAD | 0.602117 | 0.386952 | 1.054075 |
| Matched support | 42 | M1 / MAD | 0.605198 | 0.105448 | 1.107180 |
| Fixed strict V | 41 | M0 / MAD | 0.664594 | 0.260585 | 0.819450 |
| Reselected strict V | 45 | M0 / MAD | 0.674547 | 0.281061 | 0.839648 |

The M0/SD row changes scale; the matched M0/M1 rows use the same 42 identities but different model/support; fixed strict-V applies a rule to primary identities; reselected strict-V changes the paired cohort. These comparisons answer different sensitivity questions. In particular, the matched M0–M1 difference must not be attributed causally to age.

### Primary intervals

All 12 primary intervals are in Table 2. The P2/P3 percentile width comparison was 0.412591 versus 0.406597 for ICC (P3/P2 0.9855), 0.374731 versus 0.368696 for mean change (0.9839), and 0.387236 versus 0.570940 for RMS displacement (1.4744). Thus the P3 RMS interval was 47.4% wider in this realized dataset. This is not a test of superiority and does not identify a pure reference-variance component. Figure 1 displays the three percentile endpoint-specific axes.

| Endpoint | Family | P2 95% interval | P3 95% interval | P2 width | P3 width |
|---|---|---|---|---:|---:|
| ICC(A,1) | Percentile | 0.373238 to 0.785829 | 0.380418 to 0.787014 | 0.412591 | 0.406597 |
| ICC(A,1) | Basic | 0.451994 to 0.864585 | 0.450809 to 0.857406 | 0.412591 | 0.406597 |
| Mean level change | Percentile | 0.181831 to 0.556562 | 0.178146 to 0.546841 | 0.374731 | 0.368696 |
| Mean level change | Basic | 0.174774 to 0.549505 | 0.184495 to 0.553191 | 0.374731 | 0.368696 |
| RMS shape displacement | Percentile | 0.810596 to 1.197831 | 0.800800 to 1.371739 | 0.387236 | 0.570940 |
| RMS shape displacement | Basic | 0.805460 to 1.192696 | 0.631553 to 1.202492 | 0.387236 | 0.570940 |

### Repaired confirmatory simulations

Figure 2 and Table 3 show the confirmatory MAD-scale RMS percentile comparison. In S1, P2 covered 1,606/2,000 available intervals (0.803, MCSE 0.00890), and P3 covered 1,835/2,000 (0.9175, MCSE 0.00615); both had availability 1.000. The paired P2-minus-P3 coverage difference was -0.1145 (MCSE 0.00723), and P2-minus-P3 width difference was -0.10036 (MCSE 0.00055). P3 was better in this S1 cell but was still below the nominal 0.95 target.

In S5, P2 availability was 1,994/2,000 (0.997), conditional coverage 0.918756, and available-and-covered 0.916. P3 availability was 1,260/2,000 (0.630), conditional coverage 0.956349, and available-and-covered 0.6025. P2-minus-P3 availability was 0.3670 (MCSE 0.01078) and available-and-covered difference was 0.3135 (MCSE 0.01128). P3 conditional coverage cannot be interpreted without its substantial unavailability. Failure summaries are supplied with the C3 aggregate tables; S6 specifically induces MAD structural undefinedness by construction.

| Scenario / method | Availability | Conditional coverage | Available and covered | Mean width |
|---|---:|---:|---:|---:|
| S1 P1 | 1.0000 | 0.9385 | 0.9385 | 0.14706 |
| S1 P2 | 1.0000 | 0.8030 | 0.8030 | 0.15454 |
| S1 P3 | 1.0000 | 0.9175 | 0.9175 | 0.25490 |
| S1 P4 | 1.0000 | 0.9130 | 0.9130 | 0.24841 |
| S5 P1 | 1.0000 | 0.9190 | 0.9190 | 0.12599 |
| S5 P2 | 0.9970 | 0.918756 | 0.9160 | 0.12622 |
| S5 P3 | 0.6300 | 0.956349 | 0.6025 | 0.14111 |
| S5 P4 | 0.6495 | 0.936875 | 0.6085 | 0.13310 |

Pilot results for S2–S4/S6 are exploratory only and remain available in the repaired complete 384-cell synthesis table; they are not elevated to confirmatory evidence.

All three endpoints are represented in Supplementary Table S1 (`supplementary_tables/confirmatory_all_endpoint_tradeoffs.csv`). In S1, P2/P3 conditional coverage was 0.9360/0.9425 for ICC and 0.9325/0.9365 for mean level change, with availability 1.000 for both. In S5, P2/P3 availability was 0.997/0.630 for every MAD percentile endpoint. Thus the contrast is endpoint- and mechanism-specific, rather than evidence that RMS alone is validated.

## Discussion

The linked evidence supports a narrow conclusion. Holding a transform fixed and refitting it can yield different interval behavior, and evaluation should report conditional coverage and interval availability. Because oracle-conditional P1 is also below nominal in several S1/S5 cells, the contrast cannot be attributed solely to reference refitting. S1 illustrates a setting where P3 improves RMS coverage over P2 but remains subnominal. S5 illustrates near-nominal P3 RMS conditional coverage among successful draws alongside substantial unavailability. Neither result licenses a general claim that P3 is calibrated or superior.

This work builds directly on established profile, ICC, cross-fitting, bootstrap, and simulation-reporting literature. Its candidate contribution is the failure-aware integration of those methods for a cross-fitted five-field reference transformation and three longitudinal profile summaries, with repaired simulation records and a reproducible empirical illustration. A targeted literature search did not identify this exact combination; that is a search result, not proof of absence of prior work.

The Penn LEAD illustration shows moderate absolute agreement in profile level, a positive occasion-ordered average level difference, and nonzero centered-shape displacement. The transformed-unit level difference cannot be separated into development, practice, selection, measurement, or other effects. Practice effects are documented in longitudinal neurocognitive research and in work using the Penn CNB, making causal developmental wording especially inappropriate. RMS is nonnegative and includes measurement variability; a positive RMS interval alone is not proof of genuine individual change. Correlation of centered shapes likewise cannot establish person-level profile reliability.

The measurement limitations are consequential. `cnb_lnb_mcr` is documented as 1- and 2-back true positives with range 0–20, but its occasion-specific denominator and form composition are not established. `cnb_ctap_dom` is a mean of dominant-hand trials, but unit and exact aggregation are not established. The examined sources do not provide a task-version/scoring-equivalence crosswalk for all five fields. Session labels establish order, not precise elapsed time. Complete-case and support restrictions also limit generalizability. The manuscript therefore reports fields and earlier/later occasions rather than equivalence, rates, normative interpretations, or developmental trajectories.

A further experiment is only needed if the intended claim expands to calibration across empirically documented score mechanisms. It would require a prespecified, metadata-informed mixed simulation of field bounds, ties, form composition, and reference support, with success defined jointly by near-nominal coverage and high availability. That experiment is not needed for the present narrow manuscript and was not performed.

## Data and code availability

The underlying resource is the released Penn LEAD ds007116 material available in the local project and its documented public data sources. This draft refers to frozen C1/C2 and B3-R artifacts and reuses C3 public aggregate tables and figures. The C4 package supplies the manuscript, claim-source matrix, measurement evidence, references, and paths to the validated figure sources. No new public repository, DOI, or participant-level data release is claimed.

## References

Carpenter J, Bithell J. Bootstrap confidence intervals: when, which, what? A practical guide for medical statisticians. *Statistics in Medicine*. 2000;19:1141–1164. doi:10.1002/(SICI)1097-0258(20000515)19:9<1141::AID-SIM479>3.0.CO;2-F.

Chernozhukov V, Chetverikov D, Demirer M, et al. Double/debiased machine learning for treatment and structural parameters. *The Econometrics Journal*. 2018;21:C1–C68. doi:10.1111/ectj.12097.

Cronbach LJ, Gleser GC. Assessing similarity between profiles. *Psychological Bulletin*. 1953;50:456–473. doi:10.1037/h0057173.

Ibrahim I, Tobar S, Elassy M, et al. Practice effects distort translational validity estimates for a neurocognitive battery. *Journal of Clinical and Experimental Neuropsychology*. 2015;37:530–537. doi:10.1080/13803395.2015.1037253.

McGraw KO, Wong SP. Forming inferences about some intraclass correlation coefficients. *Psychological Methods*. 1996;1:30–46. doi:10.1037/1082-989X.1.1.30.

Morris TP, White IR, Crowther MJ. Using simulation studies to evaluate statistical methods. *Statistics in Medicine*. 2019;38:2074–2102. doi:10.1002/sim.8086.

Sevchik BL, Shafiei G, Murtha K, et al. A longitudinal data resource to study brain development and transdiagnostic variation in executive function. *Scientific Data*. 2026. doi:10.1038/s41597-026-08095-1.

Slade PD, Townes BD, Rosenbaum G, Martins IP, Luis H. The serial use of child neurocognitive tests: development versus practice effects. *Psychological Assessment*. 2008;20:361–369. doi:10.1037/a0012950.

Sullivan EV, Brumback T, Tapert SF, et al. Effects of prior testing lasting a full year in NCANDA adolescents. *Developmental Cognitive Neuroscience*. 2017;24:72–83. doi:10.1016/j.dcn.2017.01.003.

## Figure and table callouts

Table 1 is the 18 planned empirical point estimates; Table 2 is the 12 primary intervals; Table 3 is the confirmatory RMS tradeoff. Figure 1: primary empirical intervals. Figure 2: confirmatory coverage/availability tradeoff. Figure 3: descriptive sensitivity estimates. Source paths and captions are in `TABLE_AND_FIGURE_MAP.md`.
