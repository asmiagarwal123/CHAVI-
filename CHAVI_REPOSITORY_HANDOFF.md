# CHAVI repository handoff

**Document version:** 1.0  
**Inspection date:** 2026-10-07 (Asia/Calcutta)  
**Repository root inspected:** `C:\Users\asmi\Desktop\Projects\CHAVI`  
**Audience:** an AI agent with no prior CHAVI context  
**Purpose:** standalone, evidence-linked description of the completed repository; this document does not change the research, rerun analyses, or authorize publication.

## 1. Read this first

CHAVI is a completed, bounded methodological and reproducibility study of uncertainty in longitudinal five-task cognitive profiles. Its final scientific question is:

> When five repeated task scores are transformed against an internally estimated, cross-fitted reference, how do bootstrap procedures that hold that reference transformation fixed differ from procedures that resample and refit it, for level agreement, mean level change, and centered-shape displacement?

The final contribution is failure-aware reporting of interval coverage together with interval availability and the joint probability that an attempted interval is both available and covers truth. The Penn LEAD analysis is a descriptive empirical illustration, not a clinical, causal, diagnostic, normative, or individual-reporting system. This framing is the one in `chavi_analysis_ds007116_step5bc6final_fee_erratum_20261003/FACULTY_REVIEW_HANDOFF.md` and `chavi_analysis_ds007116_step5bc3_scientific_synthesis_20261003/FINAL_SCOPE_AND_RESEARCH_QUESTION.md`.

The most important provenance fact is that several September root handoffs describe the project as blocked after a faulty transformation lineage. That was true then, but it is no longer the current state. The October recovery, clean rebuild, repaired simulations, empirical execution, synthesis, and faculty package supersede that status. Use this authority chain:

1. pinned dataset and verified staged payload hashes;
2. Step 3B source rows and October source reconstruction;
3. `chavi_analysis_ds007116_step5ba_clean_rebuild_20261001/` for transformation;
4. `chavi_analysis_ds007116_step5bb3r_validation_repair_20261002/` for simulation results;
5. `chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003/` for the adopted empirical protocol;
6. `chavi_analysis_ds007116_step5bc2_empirical_execution_20261003/` for empirical numbers;
7. Step 5B-C3 for synthesis and Step 5B-C6-FINAL fee-erratum for the current faculty-review package.

`CHAVI_PROJECT_INDEX.md` records this chain. The old transformed-data, BAR2, BAR3, and original B3 results remain in place for auditability; do not silently substitute them for the authoritative packages named above.

## 2. Repository and inspection state

### 2.1 Git state

The CHAVI project root has no `.git` directory. Root project branch, commit, status, and project-wide Git history are therefore **UNKNOWN / UNAVAILABLE**. Running Git discovery at the root falls through to a broken parent worktree and fails with `fatal: cannot change to 'C:/Users/asmi'`; this is not evidence of a CHAVI commit.

The nested dataset `ds007116/` is a Git checkout and was inspected directly on 2026-10-07 with a command-local safe-directory override:

| Property | Verified value |
|---|---|
| Branch | `main` |
| Commit | `fc7dc36fa2598b0b2e4579baef37d148cc085207` |
| Exact tag | `1.0.6` |
| Status | `## main...origin/main`, no porcelain changes |
| Latest recorded commit | `[OpenNeuro] Recorded changes`, 2026-07-28T02:35:41Z |

Historical project change chronology must be reconstructed from dated milestone directories, manifests, correction reports, hashes, and archives—not from a root Git log.

### 2.2 Inspection coverage

The workspace contains about 30,778 non-environment files. Inspection covered:

- all root project documentation and the generated inventory;
- all 35 top-level milestone/recovery/staging directories and their root manifests, reports, contracts, scripts, tests, results, validation records, and logs;
- the authoritative transformation, simulation, empirical, synthesis, manuscript, and faculty packages in depth;
- dataset root metadata, phenotype dictionaries, staged phenotype payload evidence, BIDS subject/session organization, and derivative inventory;
- all 15 root ZIP archives and available hash/verification sidecars;
- the local Python environment and dependency declarations;
- nested dataset Git identity/status/history.

There are 146 project Python scripts, 21 `test*.py` scripts, 132 log/out/err files, 16 PDFs, and no `.ipynb` notebooks. Imaging binaries and generated derivative maps under `ds007116/sub-*` and `ds007116/derivatives/` were inventoried by path/type and sampled through metadata; their voxel contents were not scientifically reanalyzed because CHAVI does not use imaging data. Dependency/cache internals (`.venv`, `.uv-cache`, `__pycache__`, `.pytest_cache`) were identified but excluded from detailed review.

No scientific pipeline, experiment, test suite, output generator, archive builder, publication action, or dependency installation was run during this handoff audit. Read-only environment/version, Git, file, JSON, CSV, code-symbol, hash-sidecar, and report inspection commands were run. The only files intentionally created or regenerated for this task are stated in §18.

## 3. Scientific purpose, boundaries, and final status

CHAVI uses five repeated Penn Computerized Neurocognitive Battery score fields from Penn LEAD to study reference-scaled profile level and relative shape. It evaluates how uncertainty from estimating the reference transformation affects bootstrap intervals.

The project does **not**:

- diagnose ADHD, psychosis, autism, or any condition;
- infer a participant's permanent strengths/weaknesses or clinical change;
- establish population norms or clinical z-scores;
- treat the five task fields as five validated latent domains;
- identify practice, development, intervention, or causal effects;
- use MRI, DWI, ASL, fMRI, EEG, gaze, audio/video, deep learning, or prediction;
- authorize individual reporting, an Evidence Engine, or a clinical UI.

The correct term is **longitudinal agreement/dependability**, not pure short-interval test–retest reliability. Repository session timing is rounded/anonymized and intervals are long/nonuniform; development, practice, state, administration, true change, and error cannot be separated.

Current documented status:

- source retrieval/audit, task-level agreement, transformation, known-truth simulation, empirical profile analysis, independent validation, synthesis, and manuscript drafting are complete;
- the authoritative manuscript is a faculty-review draft, not a journal submission;
- authorship, affiliations, ethics/data-use determination, funding/conflicts, journal/fee decision, and public archiving permissions remain author-controlled and unresolved;
- measurement metadata for LNB denominator/load, CTAP physical unit/exact aggregation, and cross-occasion task-version equivalence remain unresolved.

Evidence: `chavi_analysis_ds007116_step5bc2_empirical_execution_20261003/readiness_verdict.json` (`status: PASS`, verdict `EMPIRICAL ANALYSIS COMPLETE AND INDEPENDENTLY VALIDATED`) and `chavi_analysis_ds007116_step5bc6final_fee_erratum_20261003/READY_FOR_FACULTY_REVIEW.md`.

## 4. Dataset, provenance, variables, QC, and cohorts

### 4.1 Dataset identity and staging

| Item | Value and evidence |
|---|---|
| Dataset | Penn LEAD: Penn Longitudinal Executive functioning in Adolescent Development |
| Accession/snapshot | OpenNeuro `ds007116`, tag `1.0.6` |
| Pinned commit | `fc7dc36fa2598b0b2e4579baef37d148cc085207` |
| DOI | `10.18112/openneuro.ds007116.v1.0.6` |
| BIDS/license/type | BIDS 1.8.0, CC0, raw |
| Registered participants | 132 |
| Recorded session rows | 225 |
| Participants with 1 / 2 / 3+ recorded sessions | 59 / 53 / 20 |
| Phenotype payloads | 41/41 staged, size- and SHA-256-verified against pinned Git-annex keys |
| Cognitive source coverage | 219 participant-session keys across 131 participants; 70 participants repeated before five-task restriction |

Dataset metadata are in `ds007116/dataset_description.json`, `ds007116/README`, `ds007116/participants.tsv`, and `ds007116/participants.json`. Retrieval evidence is in `chavi_audit_ds007116_step1b_20260907/retrieval_manifest.csv` and `payload_verification_report.md`. Payloads were retrieved from the official OpenNeuro S3 phenotype prefix into `chavi_step1b_phenotype_staging_20260907/`, then checked against content-addressed annex keys; the pointer checkout was not overwritten. Exact original download method/date before this staged retrieval is **UNKNOWN**.

The dataset includes multimodal imaging and derivatives, but CHAVI's analytical input is phenotype tabular data only. Scanner n-back events are explicitly separate from the phenotype `short_letter_2back.tsv` score table.

### 4.2 Exact task variables and directions

All directions are +1 (higher raw value is treated as better task performance). Do not rename these as validated domains.

| Order | Task key | Source table | Score field | QC field | Observed range | Meaning/boundary |
|---:|---|---|---|---|---|---|
| 1 | `letter_nback` | `short_letter_2back` | `cnb_lnb_mcr` | `cnb_lnb_valid_code` | 6–20 | True-positive response count for 1- and 2-back trials; denominator/load composition unresolved; not normalized accuracy |
| 2 | `face_memory` | `penn_face_memory_test` | `cnb_cpf_cr` | `cnb_cpf_valid_code` | 19–40 | CPF total correct responses |
| 3 | `matrix_reasoning` | `penn_matrix_reasoning_test` | `cnb_pmat_cr` | `cnb_pmat_valid_code` | 1–24 | PMAT total correct responses |
| 4 | `emotion_recognition` | `penn_emotion_recognition_task` | `cnb_er40_cr` | `cnb_er40_valid_code` | 15–40 | ER40 total correct responses |
| 5 | `dominant_finger_tapping` | `short_computerized_finger_tapping_task` | `cnb_ctap_dom` | `cnb_ctap_valid_code` | 34.33333–89.66667 | Mean dominant-hand trial value; physical unit/exact aggregation unresolved |

Evidence: `chavi_analysis_ds007116_step5a_measurement_specification_20260916/score_semantics_and_direction.csv`, the five `ds007116/phenotype/*.json` dictionaries, and `step5ba_rebuild_contract.json` key `tasks`.

### 4.3 QC and missingness rules

Local task dictionaries define: `V` = Valid; `F` = Likely valid, with a limited/mild-to-moderate problem; `N` = Not Valid; `X` = Excluded; `S` = Skipped; `0` = no autovalidation rule; `C` = assessor comment. The primary V/F policy requires a finite selected score and all applicable exact QC fields to be `V` or locally documented likely-valid `F`. `N/X/S` are excluded; `0/C/VC`, unknown, missing, partial, or absent applicable QC are unresolved and excluded from the primary. Strict-V requires raw `V` for all relevant rows. Invalidity is not inferred by substring matching—the earlier bug admitting `Not Valid` records was repaired in Step 3A.

There is no primary imputation, winsorization, silent extreme removal, score reversal, outcome-driven selection, or missing-value replacement. Missing/unresolved QC remains distinct from invalid/skipped. The QC field is documented at table level; score-specific scope remains unresolved. Evidence: `chavi_audit_ds007116_step3a_20260907/qc_policy_draft.yaml`, `qc_policy_draft.csv`, `eligibility_change_trace.csv`, and Step 3B `task_observations_long.csv` fields.

Step 3B contains 1,095 unique participant/session/task source rows. It records raw and parsed score, raw QC code and interpreted meaning, policy eligibility/reason, missingness, age/timing caveats, comparability, and source-row reference. It produced no standardization or inference.

### 4.4 Occasion ordering, continuations, and pairing

Sessions are ordered by numeric occasion order from `assessment_occasion_mapping_step3a.csv` and the frozen identity map, not by input row order or lexical sorting. One dataset-documented session is a continuation/repeat a few days after an incomplete session and cannot create a new cognitive occasion; the exact identity is retained only in protected source/audit records. The empirical execution freezes exact ordered pairs in `c2_execution_specification.json` key `ordered_occasion_keys`; public documents must not disclose participant identities.

Primary pairing uses the first two jointly complete, non-continuation, synchronized five-task V/F occasions. Reselected strict-V chooses the first two strict-V complete occasions and can change the visit pair; fixed-pair strict-V retains the primary pair and requires all ten task records to be `V`. Thus reselected strict-V is not a pure QC-only comparison. Four pair changes are documented in `qc_pairing_sensitivity_identity_comparison.csv` but must not be copied into public reports.

### 4.5 Cohort and denominator reconciliation

| Population/record type | Participants | Occasions | Task rows | Meaning |
|---|---:|---:|---:|---|
| Registered dataset | 132 | 225 recorded session rows | — | dataset registry |
| Represented in five-task source | 131 | — | 1,095 source rows | source availability, not eligibility |
| Complete synchronized V/F pool | 109 with ≥1 | 176 | 880 task records | jointly complete eligible occasions |
| Reference A | 109 | 109 | 545 | earliest complete V/F non-continuation occasion |
| Primary V/F | 52 | 104 | 520 | first two complete V/F occasions |
| M1-supported matched subset | 42 | 84 | 420 | both occasions supported for M1; M0 comparator uses same identities |
| Reselected strict-V | 45 | 90 | 450 | first two complete strict-V occasions |
| Fixed-primary-pair strict-V | 41 | 82 | 410 | primary visits retained; all ten records strict V |

The often-confused 50/52/53 figures refer to different constructions: 53 participants have a separately eligible pair for every task; 50 have the same selected session labels across all five task-specific pairs; 52 have two jointly complete synchronized profiles under profile-first construction. They are not contradictory.

The transformation output expands each physical task record across 2 models × 2 scales. Across the three analytical strata it contains 1,380 stratum-specific source rows, 5,520 expanded long rows, and 1,104 expanded wide occasion rows. The unique physical-source union is 540 task records. Expanded records are analytical representations, not new participants, occasions, or observations. Evidence: `CLEAN_REBUILD_AND_VALIDATION_REPORT.md` and `denominator_and_identity_reconciliation.csv`.

## 5. Architecture and data flow

```text
ds007116/ metadata + Git-annex pointers
        +
chavi_step1b_phenotype_staging_20260907/ verified phenotype payloads
        ↓
Steps 1B–3A audits/specification/QC correction
        ↓
Step 3B source tables and explicit participant/session/task keys
        ├──→ Step 4A/4B task-level agreement
        ↓
Step 5A measurement specification and R2 decision evidence
        ↓
September transformation branch → forensic audit → superseded/quarantined
        ↓
October preflight correction → adopted Design-B clean rebuild (5B-A)
        ├──→ B1 estimand/bootstrap protocol
        ├──→ B2 pilot → B3 confirmatory → B3-R authoritative repair
        ↓
C1 frozen empirical protocol → C2 validated empirical execution
        ↓
C3 synthesis/figures → C4 draft → C5 revision → C6 faculty package
        ↓
C6-FINAL fee erratum (current review package)
```

Important top-level paths:

| Path | Role |
|---|---|
| `ds007116/` | pinned BIDS/OpenNeuro dataset and imaging derivatives |
| `chavi_step1b_phenotype_staging_20260907/` | materialized verified phenotype TSV payloads |
| `chavi_audit_ds007116_*` | sequential source audits, QC/specification work, Step 3B analysis-preparation tables |
| `chavi_analysis_ds007116_step4*` | task-level longitudinal agreement and independent reviews |
| `chavi_analysis_ds007116_step5a*` | profile measurement specification, decision evidence, historical contract/transform branch |
| `chavi_recovery_phase1_forensic_audit_20260916/` | detected September lineage/independence defects |
| `chavi_recovery_preflight*20261001/` | reconstructed source cohorts and corrected cross-fit interpretation |
| `chavi_analysis_ds007116_step5ba_clean_rebuild_20261001/` | authoritative transformations and independent validation |
| `chavi_analysis_ds007116_step5bb1_profile_protocol_20261001/` | estimand geometry and bootstrap protocol foundation |
| `chavi_analysis_ds007116_step5bb2_simulation_pilot_20261002/` | 600-outer implementation pilot |
| `chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002/` | historical confirmatory run; affected results superseded by B3-R |
| `chavi_analysis_ds007116_step5bb3r_validation_repair_20261002/` | authoritative repaired simulation tables and validators |
| `chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003/` | frozen empirical contract; no results |
| `chavi_analysis_ds007116_step5bc2_empirical_execution_20261003/` | authoritative empirical participant-linked audit and public aggregate results |
| `chavi_analysis_ds007116_step5bc3_scientific_synthesis_20261003/` | authoritative synthesis, aggregate tables, figures, literature positioning |
| `chavi_analysis_ds007116_step5bc4*`, `step5bc5*`, `step5bc6*` | manuscript development and review packaging |
| `chavi_analysis_ds007116_step5bc6final_fee_erratum_20261003/` | current faculty-review package plus publication-fee correction |
| `PROJECT_ARCHITECTURE.md` | generated exhaustive filesystem inventory; authoritative map of present files |
| root ZIPs/sidecars | frozen milestone packages and SHA-256/verification records |

## 6. Chronological completed work

1. **Dataset audit and retrieval (2026-09-07).** Step 1/1B identified the 1.0.6 snapshot, registered/session counts, imaging and phenotype inventory, staged all 41 phenotype TSVs, matched size/SHA-256 annex keys, classified 21 cognitive and 20 questionnaire/outcome tables, and built variable/QC/missingness inventories.
2. **Feasibility and QC specification (Steps 2, 2B, 2C).** Candidate scores, occasion mappings, exact QC meanings, exclusion flows, pair manifests, and outcome availability were evaluated. These stages were feasibility/specification work, not final inference.
3. **QC repair and preparation (Steps 3A, 3B).** Substring handling that admitted `Not Valid` was repaired. Step 3B generated the 1,095-row source table, pair/profile manifests, outcome rows, dictionaries, and cohort reconciliation. Proposed prediction fields exist only as availability/preparation artifacts; no prediction model was run.
4. **Task-level agreement (Steps 4A/4B, 2026-09-14–16).** Face Memory and then all five tasks were analyzed with participant-pair bootstraps and independently reconstructed. These results remain valid narrow task-level evidence.
5. **Profile specification and decision evidence (Step 5A through 5A-D-R2).** Cohorts, exact fields/directions, level/scatter/shape geometry, M0/M1 candidates, SD/MAD diagnostics, support, uncertainty, and caveats were specified. R2 recorded evidence, but its historical bootstrap/fold claims did not by themselves validate later production.
6. **Historical contract and failed September branch (5A-F, 5B-A/BAR2/BAR3).** A contract/approval record and transformed outputs were produced. The forensic audit found conflicting reference/fold semantics, mixed denominators, incomplete M1 lineage, and non-independent validators. These files remain forensic history and are not authoritative results.
7. **Recovery audit and October preflights.** The first preflight reconstructed sources but interpreted Reference-A folding as 109-way Design A. The corrected preflight demonstrated three distinct designs. The researcher adopted **Design B**: fold the 52 targets and keep 57 auxiliaries in every applicable reference fit.
8. **Clean transformation rebuild (5B-A, 2026-10-01).** The adopted contract was frozen; sources, three strata, target folds, M0/M1 × MAD/SD parameters, support/fallback, long/wide outputs, schemas, manifests, independent calculations, determinism, and preservation were completed and passed.
9. **Profile protocol (5B-B1).** Four-dimensional shape geometry, estimands, degeneracy rules, ICCs, trace statistic, identity-linked resampling, output schemas, and synthetic validation were completed. B1 was initially labeled recommended; C1 later adopted the empirical protocol.
10. **Simulation pilot (5B-B2, 2026-10-02).** Six scenarios × 100 outer datasets, four procedures, two scales, three endpoints, 499 attempts, and two interval families completed as an implementation pilot.
11. **Confirmatory simulation (5B-B3).** A corrected pilot and 2,000-outers-per-scenario confirmatory evaluation for S1/S5 completed, but later audit found four validation/implementation defects.
12. **Simulation validation repair (5B-B3-R).** Defects were reproduced, the narrow mechanics repaired without changing frozen streams or estimands, affected same-stream outers recalculated, all tables reconciled, truth reproduced, checkpoint/resume verified, and authoritative repaired outputs frozen.
13. **Empirical protocol (5B-C1, 2026-10-03).** Exact inputs, hashes, estimands, P2/P3 uncertainty procedures, interval gates, tolerances, missingness/support, and reporting limits were frozen. Dry run verified 52/104/520 but calculated no empirical endpoint.
14. **Empirical execution (5B-C2).** Six prespecified analysis slices, 18 point estimates, 999 P2 and 999 P3 bootstrap attempts, 12 intervals, profile-correlation summary, participant-linked provenance, independent calculation, fresh-process reproduction, and resume checks completed.
15. **Synthesis and publication decision (5B-C3).** Frozen B3-R and C2 evidence was reconciled; aggregate tables and three publication figures were generated; claims/literature/limitations were mapped; a bounded manuscript was recommended.
16. **Manuscript packages (C4–C6-FINAL).** C4 created the first Markdown draft and corrected the Penn LEAD descriptor to the 2026 published article. C5 performed skeptical revision and added a reproducibility supplement. C6 assembled faculty-review tables/figures/checklists. C6-FINAL corrected citation/package issues; the fee-erratum package then corrected unsupported journal-fee wording without changing science.

## 7. Implemented transformation and profile methods

### 7.1 Cross-fitted reference transformation

Reference A has 109 participants: 52 longitudinal analysis targets plus 57 reference-only auxiliaries. With NumPy seed 42, sorted target IDs are permuted and assigned by permutation index modulo five. Target fold sizes are 11/11/10/10/10. For each target fold, its targets are excluded while all 57 auxiliaries and targets in other folds remain, so fitting counts are 98/98/99/99/99. Both visits of a target retain one fold. This is `reference_design: B_target_plus_auxiliary` in `step5ba_rebuild_contract.json`.

The 87/88 fits in the first preflight correspond to Design A (fold all 109). The 41/42 fits correspond to target-only Design C. Neither is the adopted primary implementation. The corrected provenance is explicit in `chavi_recovery_preflight_correction_20261001/CORRECTED_PREFLIGHT_AND_DECISION_REVIEW.md`.

For task `j`, held-out target `i`, occasion `t`, and that target's training fold:

- M0 center: `mu_j = arithmetic mean(y_j)`;
- normal-consistent MAD: `s_MAD,j = median(|y_j - median(y_j)|) / 0.6744897501960817`;
- SD sensitivity: sample SD with `ddof=1`;
- primary coordinate: `z_ijt = direction_j (y_ijt - mu_j) / s_j` (all directions are +1).

M1 fits OLS with intercept on finite Step 3B `session_age` in the same fold-specific training set. Its coordinate is the prediction residual divided by the training residual MAD (or SD sensitivity). The inclusive support interval is the fold-specific minimum/maximum finite training age. Missing/out-of-support M1 coordinates remain null with reason; the separately labeled M0 fallback field may be populated, but it is never inserted as M1. M0 age support is not applicable. Source: `run_clean_rebuild.py` functions `mad`, `sd`, `scale_status`, and the M0/M1 blocks; independent replication is in `independent_validator.py`.

All 100 parameter records (5 folds × 5 tasks × 2 models × 2 scales) were supported. Across expanded rows M0 had no unsupported values. M1 had 280 unsupported stratum/model/scale records outside inclusive training-age support: per scale, 50 in primary, 50 reselected strict-V, and 40 fixed-pair strict-V (10, 10, and 8 per task respectively). M1-complete participant pairs per scale were 42/52 primary, 36/45 reselected strict-V, and 33/41 fixed-pair strict-V.

### 7.2 Profile geometry and change

For a five-task coordinate vector `z`:

- level/elevation: `L = mean(z)`;
- centered relative shape: `q = z - L1`, so `sum(q)=0`;
- scatter: `S = sqrt(q'q / 5)`;
- fixed Helmert contrasts: `c = H' z`, where the 5×4 orthonormal Helmert matrix has column `k` equal to `1/sqrt(k(k+1))` in rows 1…k, `-k/sqrt(k(k+1))` in row k+1, and zero afterward;
- reconstruction/energy: `q = Hc`, `q'q = c'c`, and `z'z = 5L² + c'c`.

Thus the five centered entries occupy a four-dimensional subspace; they are not five independent components. For occasion 2 minus occasion 1:

- participant level change: `ΔL_i = L_i2 - L_i1`;
- scatter change: `ΔS_i = S_i2 - S_i1`;
- participant shape displacement: `sqrt(||q_i2-q_i1||²/5)`;
- total displacement: `sqrt(||z_i2-z_i1||²/5)`, with `D_total² = ΔL² + D_shape²`.

The reported sample RMS centered-shape displacement is pooled, not a mean of participant RMS values:

`RMS_shape = sqrt[(1/(5n)) Σ_i Σ_j (q_ij2-q_ij1)²]`.

Mean level change is `n^-1 Σ_i ΔL_i`. Participant profile correlation is Pearson correlation between two centered five-coordinate shapes and is descriptive only. It is undefined when either shape norm is at or below `64*eps*max(||z||, sqrt(5)|L|, tiny)`. Evidence: `profile_estimands.py` (`profile_geometry`, `pair_geometry`, `profile_correlation`) and the C1/C2 contracts.

### 7.3 ICC

For `n` participants and `k=2` occasions, CHAVI uses two-way mixed-effects, single-measure, absolute-agreement ICC(A,1):

`ICC(A,1) = (MSR-MSE) / [MSR + (k-1)MSE + k(MSC-MSE)/n]`.

Degrees of freedom are `(n-1, 1, n-1)`. ICC(C,1) is implemented descriptively as `(MSR-MSE)/(MSR+(k-1)MSE)` but is not interchangeable with the primary absolute-agreement estimand. Negative ICCs are retained; undefined ICC does not automatically invalidate mean change or RMS. Evidence: `profile_estimands.py` functions `icc_a1`, `icc_c1` and `c2_analysis.py` functions `stable_icc`, `endpoints`.

## 8. Bootstrap procedures and empirical execution

P2 (`P2_fixed_transform`) resamples the 52 target identities with paired visits and holds the fitted M0/MAD transformation fixed. P3 (`P3_joint_unstratified`) uses the same linked target multiplicities for analysis and target-reference roles, an independently keyed auxiliary draw shared across represented folds, fixed original fold membership, and complete held-out-target exclusion, then refits the reference transformation. Duplicate sampled identities are frequency weights; visits remain clustered. Failed draws are never redrawn.

The empirical contract uses 999 attempts, 95% percentile and basic intervals, and NumPy linear quantiles. Percentile is `[q.025,q.975]`; basic is `[2θhat-q.975, 2θhat-q.025]`. The interval gate requires at least 950 valid values, at least 20 observations in each nominal tail, a finite point estimate, and no malformed input/software failure. Empirical truth and coverage are unknowable and are not reported. `run_empirical.py` lines implementing `np.quantile(..., method='linear')` and basic reflection are the executable evidence.

Checkpoint files are cumulative and written atomically. Resume selects the greatest compatible completed checkpoint after exact provenance validation; incompatible/incomplete checkpoints are rejected. The participant-linked records are private audit material under `results/participant_linked_audit/`; public aggregate outputs are in `results/public_aggregate/`.

## 9. Known-truth simulation

### 9.1 Data-generating mechanisms and truth

All scenarios have 52 targets, 57 auxiliaries, target fold counts 11/11/10/10/10, five task means `(10,12,14,16,18)`, level variance 0.5, four-dimensional shape covariance `0.5 I4`, and task noise covariance `0.5 C`, where `C[j,k]=0.3^|j-k|`. Identities are independent; level, shape, and noise are mutually independent; visit errors are independent. Unless noted, level and shape cross-occasion correlations are 0.8.

| Scenario | Mechanism |
|---|---|
| S1 | continuous correlated level and shape, no shift |
| S2 | level correlation 0.8, shape correlation 0, no shift |
| S3 | S1 plus common +0.5 visit-2 shift |
| S4 | S1 plus +0.5 shift in first Helmert shape contrast |
| S5 | S1 followed by nearest-integer, ties-to-even rounding (`numpy.rint`) |
| S6 | each task/occasion deviation independently retained with probability 0.4 and otherwise set exactly to its task mean; 0.6 point mass makes population MAD structurally zero |

Truth targets use the population baseline-reference transformation. ICC truth is `2Cov(L1,L2)/(Var(L1)+Var(L2)+(E[L2]-E[L1])²)`; mean-change truth is `E[L2-L1]`; RMS truth is `sqrt(E[||P(Z2-Z1)||²]/5)`, `P=I-11'/5`. S1–S4 and S6/SD use analytic moments. S5 ICC/RMS use two independent 500,000-pair numerical batches; S5 mean change is exactly zero by symmetry. S6/MAD is structurally undefined and never replaced by SD or zero. Exact values and numerical SEs are in B3-R `truth_results.csv`; code is `truth_engine.py`, which imports no production helpers.

### 9.2 Procedures, streams, repetitions, and intervals

Methods are P1 oracle-reference conditional bootstrap, P2 estimated-reference fixed transform, P3 identity-linked unstratified joint refit, and P4 identity-linked fold-stratified joint refit (conditions on fold counts). Both MAD and SD and all three endpoints are evaluated.

The B2 pilot ran 6 scenarios × 100 outers = 600 outer datasets, with 499 attempts per method/scale and a minimum-valid gate of 475. It is implementation evidence, not confirmatory performance evidence.

The authoritative corrected pilot reran the six scenarios at 100 outers with 999 attempts. Confirmatory evaluation used only S1 and S5, 2,000 outers each (4,000 outer datasets), 999 attempts, minimum-valid 950, and `floor(.025*n_valid) >= 20`. Both percentile/basic families use linear quantiles and no clipping/redraw. Performance denominators are always explicit:

- conditional coverage = covered available intervals / available intervals;
- availability = available intervals / attempted outer datasets;
- available-and-covered = covered available intervals / all attempted outers;
- mean/median width are conditional on availability.

Randomness uses NumPy PCG64DXSM with master seed `20261002`. Actual stream seeds are the first 128 bits of SHA-256 over master seed, namespace, stream label, scenario, and outer; the namespace represents stage, methods share frozen multiplicity arrays, and replicate is row position. The B3 contract prose incorrectly listed stage/method/replicate as independent key parts; B3-R preserved the actual streams, documented the reconciliation in `rng_contract_reconciliation.json`, and added a stage/namespace mismatch guard.

### 9.3 Failure handling and authoritative simulation findings

Reference-fit failure makes the affected P3/P4 endpoint draw invalid with a stored reason. Active nonfinite coordinates invalidate coordinate-dependent endpoints. An absent/unrepresented fold is not fit. Negative ICC is valid. Undefined endpoints are never set to zero. A dataset interval is unavailable unless all gates pass; conditional coverage must never be quoted without availability.

Across the confirmatory stage, each method/scenario/scale/endpoint attempted `2,000×999 = 1,998,000` bootstrap endpoint values. Key repaired MAD/percentile RMS results:

| Scenario/method | Available / attempted outers | Covered / available | Conditional coverage | Available-and-covered | Mean width |
|---|---:|---:|---:|---:|---:|
| S1 P2 | 2,000/2,000 | 1,606/2,000 | 0.8030 | 0.8030 | 0.154538 |
| S1 P3 | 2,000/2,000 | 1,835/2,000 | 0.9175 | 0.9175 | 0.254894 |
| S5 P2 | 1,994/2,000 | 1,832/1,994 | 0.918756 | 0.9160 | 0.126219 |
| S5 P3 | 1,260/2,000 | 1,205/1,260 | 0.956349 | 0.6025 | 0.141109 |

P3 improves conditional RMS coverage in S1 but remains below 0.95. In S5 its apparently near-nominal conditional coverage accompanies 37% unavailability, so it is not generally superior or calibrated. Full results comprise 384 prespecified stage/scenario/scale/endpoint/method/family cells in C3 `aggregate_tables/simulation_synthesis_all_prespecified.csv`; do not generalize S2–S4/S6 pilot evidence as confirmatory.

## 10. Frozen empirical results

All values below are from C2 `results/public_aggregate/endpoint_estimates.csv` and `primary_bootstrap_intervals.csv`.

### 10.1 Point estimates and sensitivities

| Analysis | n | ICC(A,1) | Mean level change | RMS shape displacement |
|---|---:|---:|---:|---:|
| Primary M0/MAD | 52 | 0.6189115725 | 0.3656683461 | 1.0016459384 |
| Primary M0/SD | 52 | 0.5993292553 | 0.3078942214 | 0.8567142706 |
| Matched M1-support M0/MAD | 42 | 0.6021172256 | 0.3869522567 | 1.0540749227 |
| Matched M1-support M1/MAD | 42 | 0.6051975034 | 0.1054476074 | 1.1071799949 |
| Fixed-pair strict-V M0/MAD | 41 | 0.6645941511 | 0.2605853993 | 0.8194499323 |
| Reselected strict-V M0/MAD | 45 | 0.6745466696 | 0.2810606672 | 0.8396475587 |

Sensitivity rows differ in transformation and/or denominator. M0–M1 is matched on 42 identities but is not a causal age effect. Fixed and reselected strict-V answer different questions. No secondary bootstrap intervals or difference tests were run.

### 10.2 Primary uncertainty intervals

Each method/endpoint attempted 999 and obtained 999 valid estimates; all 12 intervals are available.

| Method | Endpoint | Percentile 95% interval | Basic 95% interval |
|---|---|---|---|
| P2 fixed | ICC(A,1) | [0.3732383911, 0.7858293721] | [0.4519937729, 0.8645847538] |
| P2 fixed | Mean level change | [0.1818312804, 0.5565623230] | [0.1747743693, 0.5495054119] |
| P2 fixed | RMS shape displacement | [0.8105956092, 1.1978314626] | [0.8054604142, 1.1926962677] |
| P3 joint refit | ICC(A,1) | [0.3804175634, 0.7870142390] | [0.4508089060, 0.8574055815] |
| P3 joint refit | Mean level change | [0.1781458837, 0.5468413895] | [0.1844953027, 0.5531908086] |
| P3 joint refit | RMS shape displacement | [0.8007996882, 1.3717392219] | [0.6315526549, 1.2024921886] |

The realized P3 percentile width was slightly smaller than P2 for ICC/mean change and 1.4744 times P2 for RMS; these are descriptive realized differences, not superiority tests or isolated reference-variance estimates. Empirical interval coverage is unavailable by definition.

All 52 primary profile correlations were defined: minimum −0.689392, Q1 0.120974, median 0.548854, Q3 0.874382, maximum 1.000000. Correlation measures direction after removing level and relative scatter; it is not individual reliability evidence.

Interpretation: the primary level ICC describes moderate sample-level absolute agreement under this internal transformation; mean level rose by about 0.366 internal-reference units; centered shape displaced by about 1.002 units. These quantities include all sources of longitudinal difference and have no clinical threshold.

## 11. Code and execution responsibilities

### 11.1 Source and task-level stages

| Script/package | Responsibility / principal outputs |
|---|---|
| `audit_v2.py` | verified staged phenotype retrieval, table/variable/QC/missingness inventories |
| `audit_v3.py`–`audit_v6.py` | successive score/domain feasibility, exact QC correction, executable measurement specification |
| `prepare_step3b.py` | source long tables, pair/profile manifests, dictionaries, cohort reconciliation |
| `step4a_face_memory.py` / `validate_step4a.py` | Face Memory pairing, statistics, 5,000-pair bootstrap / independent raw reconstruction |
| `run_step4b_task_analysis.py` / `validate_step4b.py` | five-task agreement, plots, 25,000 total bootstrap task-replicates / independent checks |
| `prepare_step5a_measurement_specification.py` | synchronized profile occasions, cohort flow, estimand/uncertainty specification |

### 11.2 Authoritative transformation

Execution order is `prepare_contract.py` → `run_clean_rebuild.py` → `independent_validator.py` → `validate_schemas.py` → `test_clean_rebuild.py` → `make_reports.py` → `finalize_package.py`; `orchestrate_rebuild.py` coordinates the full sequence. Inputs are Step 3B, staged payloads/dictionaries, corrected preflight manifests, and the adopted contract. Outputs are source rows, folds, 100 parameters, long/wide coordinates, support audit, independent expectations/comparisons, validation JSON, report, manifest, and ZIP. `finalize_package.py` also checks deterministic fresh-process hashes and historical preservation.

### 11.3 Profile/simulation

| Script | Responsibility |
|---|---|
| B1 `profile_estimands.py` | Helmert geometry, level/scatter/shape, ICCs, trace statistic, validators |
| B1 `prepare_profile_protocol.py` | protocol, schemas, support manifests, scientific registers |
| B1 `independent_profile_validator.py` | independent synthetic geometry/resampling checks |
| B2/B3-R `simulation_core.py` | scenario generation, keyed RNG, reference fits, transformations, endpoint formulas |
| B3-R `truth_engine.py` | independent analytic/numerical truth generation |
| B3-R `run_stage.py` | outer-dataset point/bootstrap execution and atomic records |
| B3-R `reproduce_defects.py` | reproduces the four B3 defects |
| B3-R `recalculate_affected.py` | same-stream recalculation of affected P3 outers |
| B3-R `independent_full_replicate_validate.py` | scalar explicit-expansion raw-value validation subset |
| B3-R `independent_table_reconcile.py` | full interval/performance/paired-table arithmetic reconciliation |
| B3-R `consolidate_repaired.py` | authoritative repaired output tables |

### 11.4 Empirical/synthesis/manuscript

| Script/package | Responsibility |
|---|---|
| C1 `analysis_interface.py` | validates inputs/identities/support; refuses empirical calculation in C1 |
| C1 `independent_synthetic_validator.py` | executable protocol/edge/corruption checks |
| C2 `code/c2_analysis.py` | weighted MAD fits, ICC/endpoints, validation and gates |
| C2 `code/run_empirical.py` | six point-estimate slices, 999-attempt P2/P3 bootstrap, checkpoints, public/audit outputs |
| C2 `code/independent_validate.py` | independent raw-source fits, points, replicate endpoints, intervals, linkage |
| C2 `code/reproduction_checks.py` | fresh full process and interrupted/resumed equivalence |
| C2 `code/finalize_deliverables.py` | reports, manifest, preservation and archive finalization |
| C3 `code/build_synthesis.py` | aggregate tables and three figures from frozen C2/B3-R evidence |
| C6 `code/validate_c6.py` | package source/hash/value/privacy/ZIP checks; does not rerun science |

Root `recovery_phase1_audit.py`, `independent_transformation_validator.py`, `scratch_validation.py`, and `step5bar3_engine.py` are historical/recovery utilities, not the canonical current pipeline.

## 12. Testing, independent validation, tolerances, and resume

Recorded evidence includes:

- Step 4A: raw-payload reconstruction of 59 pairs, statistics/CIs within `2e-12` after displayed rounding, two ICC paths agreeing within `1e-10`, deterministic 5,000-draw bootstrap.
- Step 4B: 286 task pairs reconstructed; zero statistical/bootstrap/pair-manifest failures. The review records 80 statistical crosschecks and 25 bootstrap metric audits; five original plot-annotation failures were corrected only in reviewed copies.
- R2: 74/74 recorded tests, but later recovery showed its folds/bootstrap did not validate the adopted Design-B implementation; retain as decision evidence only.
- Corrected preflight: 24 named tests/34 assertions; source reconstruction and preservation passed.
- Clean rebuild: 27 deterministic formula/boundary/invariant/corruption tests; 100 parameter and 5,520 coordinate comparisons; zero failures; max discrepancies `2.13e-14` and `2.84e-14`; tolerance `abs <= 1e-12 + 1e-10*abs(expected)`; 29 deterministic artifacts hash-identical in a fresh process; 596 scoped historical/source artifacts unchanged.
- B1: independent synthetic validator 24/24 and unit suite 9/9. A large-offset cancellation defect in direct `H' z` was repaired by projecting centered `q`, after which all tests passed.
- B2: 600/600 outer datasets, 9/9 mechanism checks, independent crosscheck PASS; still only a pilot.
- B3-R: all four defects reproduced; replacement corruption suite 9/9; edge suite 12/12; 203,796 raw replicate endpoint/status comparisons and 4,600 dataset hashes matched; all 220,800 interval rows plus 384 performance and 384 paired-comparison rows reconciled. This is a frozen subset of raw 999-vectors plus full exported-table verification, not independent recalculation of every raw bootstrap vector.
- B3-R repair impact: 248 affected outers (257 unique draws) regenerated; 18,381,600 P3/P4 scale-support draws screened; no availability changes and one secondary coverage-cell count change. Three-process interruption/resume/fresh checkpoints were byte-identical.
- C1: 27/27 synthetic tests, dry-run counts 52 participants/104 occasions/520 rows, no empirical estimands.
- C2: 23/23 executable tests plus unchanged C1 27/27; 25 unit fits and 520 coordinates matched Step 5B-A (max coordinate difference `2.22e-15`); independent path matched 18 point values, 5,994 replicate endpoint values/classifications, 999 linkage records, 12 intervals, and seven correlation fields with zero failures. Fresh 999-draw process matched; interrupted at 3 and resumed to 7 identically to clean 7.

Numerical tolerances for transformation and empirical validation are absolute `1e-12`, relative `1e-10`. Hash equality is exact. Scientific outputs exclude runtime/timestamps where byte determinism is claimed.

## 13. Environment and reproduction

Current inspected local environment (read-only query on 2026-10-07): Windows workspace, `.venv` CPython 3.14.0, `numpy==2.5.2`, `pip==25.2`. The root `requirements.txt` and authoritative phase requirement files pin only `numpy==2.5.2`; the rest is standard library. No pandas, SciPy, statsmodels, Jupyter, or pytest is required by the authoritative October pipeline. `.uv-cache/` is an environment cache, not scientific evidence.

Canonical documented commands (not executed during this handoff) are in each `README_REPRODUCE.md`. The current end-to-end order is:

```powershell
# Transformation (full orchestration)
& 'C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe' .\chavi_analysis_ds007116_step5ba_clean_rebuild_20261001\orchestrate_rebuild.py

# Empirical protocol checks
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\independent_synthetic_validator.py
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\analysis_interface.py --dry-run --coordinates chavi_analysis_ds007116_step5ba_clean_rebuild_20261001\primary_vf_transformed_long.csv --source chavi_analysis_ds007116_step5ba_clean_rebuild_20261001\primary_vf_source_rows.csv --model M0 --scale MAD --stratum primary_vf

# Empirical execution and validation
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\code\test_c2.py
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\code\run_empirical.py
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\code\independent_validate.py
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\code\reproduction_checks.py
.\.venv\Scripts\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\code\finalize_deliverables.py

# Current faculty-package checks only (does not rerun science)
Set-Location chavi_analysis_ds007116_step5bc6final_fee_erratum_20261003
..\.venv\Scripts\python.exe code\validate_c6.py
```

B3-R's repair-specific commands are fully enumerated in its `README_REPRODUCE.md`; run them only when intentionally reproducing the frozen simulation repair because they are computationally substantial. Documented commands can rebuild archives and scientific outputs and therefore are not mere read-only checks.

Commands actually executed for this handoff were limited to PowerShell/Git/`rg` file inspection, CSV/JSON aggregation, `.venv\Scripts\python.exe --version`, and `pip list --format=freeze`, followed by the mandatory architecture generator after writing this document. No command block above was executed.

## 14. Manuscripts, figures, tables, archives, and authority

The current reader-facing package is `chavi_analysis_ds007116_step5bc6final_fee_erratum_20261003/` and adjacent ZIP. Start with:

1. `CHAVI_FACULTY_REVIEW_MANUSCRIPT.md`;
2. `METHODS_AND_REPRODUCIBILITY_SUPPLEMENT.md`;
3. `FACULTY_REVIEW_HANDOFF.md`;
4. `REQUIREMENT_TO_EVIDENCE_CHECKLIST.md` and `WHAT_I_TRIED_TO_FALSIFY.md`;
5. `ERRATUM_FROM_C6_FINAL.md` and `READY_FOR_FACULTY_REVIEW.md`.

Its `tables/` and `figures/` are copies of validated aggregate evidence. Figure 1 presents primary empirical intervals; Figure 2 simulation trade-offs; Figure 3 empirical sensitivities. Each figure has PDF/PNG/SVG and plotting-data CSV. Participant-linked data are deliberately absent.

Authority/version notes:

- C3 owns synthesis and generated aggregate tables/figures but does not supersede C2/B3-R numerical sources.
- C4 is the first reviewable manuscript and corrects the Penn LEAD descriptor from preprint to Sevchik et al., *Scientific Data* (2026), DOI `10.1038/s41597-026-08095-1`.
- C5 is the skeptical revision and methods supplement.
- `step5bc6_faculty_review_package` is superseded by `step5bc6final_faculty_handoff` for corrections.
- `step5bc6final_fee_erratum` is the current package; it changes publication-fee wording only and explicitly preserves all scientific tables, figures, estimates, and interpretation.
- No DOCX was produced; C4 documents that dependable DOCX render verification was unavailable. Markdown is authoritative.

Key frozen archive SHA-256 values from adjacent sidecars:

| Archive | SHA-256 |
|---|---|
| 5B-B3 original confirmatory (historical input) | `18251e4b88f67c6df2d3dd4c6e427c4de0237e2081690769852c3f9a7e0bc9ff` |
| 5B-B3-R repaired simulation | `b4c781062f0105c8bcec07f8bc51908cb181a02812b13e7da2330b608df5398b` |
| 5B-C1 empirical protocol | `88283d3f62825a2ba43416783ea5df669f3c2f7294f6b9ba58116bf4bca5648d` |
| 5B-C2 empirical execution | `5d5d4fa96458bf34af24d894626ff118ef970f8a78500cc2d6171ebb9c8a32fa` |
| 5B-C3 synthesis | `f3239b074638e4529988000f0bc5b39c46f41dc0372a93e377982809bac82c04` |
| C6-FINAL faculty handoff | `501f6fb94ab6de581d89746764478297837de06e9318036e8cadb59013b37994` |
| C6-FINAL fee erratum | `83cadf6b2c349c2deabd013244d104f59ed8d224ce40483da30e73becd2ece53` |

The Step 5B-A clean rebuild ZIP is authoritative and its contract hash is `619aa1e05fedfc688484691cb1e54d363c8e8ff4a63b9a5e179d05d516ac23c6`; no adjacent root `.sha256.txt` is present for that ZIP, so use `milestone_artifact_manifest.csv` and downstream input manifests for its recorded archive/hash lineage.

## 15. Completion, partial/unknown, superseded, and protected status

### Completed and authoritative

- dataset snapshot/payload provenance and source audit;
- exact five fields, directions, V/F primary and strict-V sensitivities;
- task-level agreement analyses;
- Design-B M0/M1 × MAD/SD transformation and support outputs;
- profile level, mean change, RMS centered-shape displacement, and descriptive correlations;
- six-scenario pilot and S1/S5 confirmatory known-truth simulation;
- B3-R repair and independent validation;
- 999-attempt P2/P3 empirical intervals;
- synthesis, figures, bounded manuscript, and faculty-review package.

### Implemented but intentionally not primary / not executed empirically

- scatter, ICC(C,1), shape-trace association, and some geometry helpers exist in B1, but C1/C2 did not make them primary empirical endpoints; secondary-cohort bootstrap intervals were not run;
- P1/P4 are implemented/evaluated in simulation, not in the empirical C2 comparison;
- M1 and SD are sensitivities, not alternate primary claims;
- candidate prediction-cohort tables are data-preparation artifacts only; no predictive model exists.

### Superseded or historical-only

- root `CHAVI_MASTER_PROJECT_SPECIFICATION_AND_HANDOFF.md`, `CHATGPT_CODEX_HANDOFF.md`, `CURRENT_PROJECT_STATE.md`, `RESEARCH_STATUS.md`, and `summary.md` predate the successful October downstream work and are stale on final completion;
- September `step5ba_transformed_data`, `step5bar2`, `step5bar3`, and Step 5A-F implementation claims are retained for forensic provenance but not current outputs;
- original B3 tables are superseded where B3-R identifies affected results; use filenames ending `_repaired.csv`;
- the first October recovery preflight's Design-A recommendation was corrected before the adopted Design-B rebuild;
- C6 pre-final review package and uncorrected fee statements are superseded by C6-FINAL fee-erratum.

### Unknown / needs verification

- root project Git history/commit/status: unavailable because there is no root `.git`;
- exact original dataset download method/date before verified staging;
- LNB denominator and 1-/2-back load composition for `cnb_lnb_mcr`;
- CTAP physical unit and exact aggregation for `cnb_ctap_dom`;
- released task-version/administration equivalence across occasions;
- exact cognitive assessment elapsed time (session timestamps are rounded/anonymized);
- external generalizability, population calibration, clinical meaning, and empirical coverage;
- faculty approval, authorship, ethics/data-use determination, public archiving permission, journal acceptance, and applicable publication fee.

### Protected/frozen artifacts

Do not edit the pinned dataset checkout, staged verified payloads, historical milestone packages, authoritative contracts, results, validation records, ZIPs, or hash sidecars in place. New correction work must preserve source hashes and lineage. Participant-linked C2 audit files contain identifiers and must not be embedded in public documents or shared as aggregate outputs.

## 16. Known limitations and unsupported claims

- Primary `n=52` is small and complete-case selection can affect generalizability.
- Reference A is internal and sample-dependent; coordinates are reference-scaled units, not norms.
- Scores are partly discrete/tied and can show range restriction, ceiling/concentration, and robust-scale failure.
- Centering imposes dependence and can mechanically amplify apparent relative-shape movement.
- M1 is a cross-sectional age residualization sensitivity, not a developmental trajectory model.
- Positive mean change is not proof of practice/development; nonzero RMS is not proof of genuine individual change.
- A confidence interval excluding zero for a nonnegative displacement is not a clinical finding.
- Interval overlap is not a hypothesis test; no difference tests were performed.
- Simulation establishes behavior only under its specified mechanisms. S1/S5 are plausible probes, not verified generators of Penn LEAD.
- Conditional coverage without availability is misleading; valid empirical draws do not prove empirical calibration.
- The targeted literature search bounds novelty but is not systematic and cannot prove no prior work exists.

## 17. Source/evidence index and quick orientation

For a receiving agent, read in this order:

1. **This file**, then `CHAVI_PROJECT_INDEX.md`.
2. **Dataset/provenance:** `ds007116/dataset_description.json`, `ds007116/README`, Step 1B `payload_verification_report.md` and `retrieval_manifest.csv`.
3. **Source/QC/cohorts:** Step 3B `step3b_review_report.md`, `analysis_data_dictionary.csv`, `cohort_reconciliation.csv`; Step 5A `score_semantics_and_direction.csv`, `profile_cohort_flow.csv`.
4. **Correction lineage:** Recovery Phase 1 report, then corrected preflight `CORRECTED_PREFLIGHT_AND_DECISION_REVIEW.md`.
5. **Transformation:** clean rebuild `step5ba_rebuild_contract.json`, `CLEAN_REBUILD_AND_VALIDATION_REPORT.md`, `validation_results.json`, and `README_REPRODUCE.md`.
6. **Methods:** B1 `PROFILE_PROTOCOL_REVIEW.md`, `profile_estimands.py`, and `BOOTSTRAP_AND_REFERENCE_UNCERTAINTY_PROTOCOL.md`.
7. **Simulation:** B3-R `B3R_AUDIT_AND_IMPACT_REPORT.md`, contracts, `scenario_registry.json`, `truth_results.csv`, repaired performance/failure tables, and validation JSONs.
8. **Empirical:** C1 contract/report, then C2 `EMPIRICAL_RESULTS_AND_VALIDATION_REPORT.md`, public aggregate CSVs, readiness and independent-validation JSONs.
9. **Synthesis/manuscript:** C3 synthesis and claim matrix, then C6-FINAL fee-erratum faculty package.
10. **Filesystem detail:** `PROJECT_ARCHITECTURE.md` for the exhaustive generated inventory.

Evidence locator examples used throughout this handoff:

| Claim class | Primary locator |
|---|---|
| Dataset identity/counts | `ds007116/dataset_description.json`; Step 1B `audit_v2_report.md` |
| Payload provenance | Step 1B `retrieval_manifest.csv` and `payload_verification_report.md` |
| QC meanings/policy | Step 1B `consolidated_variable_dictionary.csv`; Step 3A `qc_policy_draft.yaml` |
| Exact task variables | Step 5A `score_semantics_and_direction.csv`; clean contract `tasks` |
| Cohorts/identities | corrected preflight reconciliation; clean contract `cohorts` |
| Transformation formulas | clean `run_clean_rebuild.py`; independent validator; contract |
| Profile formulas | B1 `profile_estimands.py`; C1 `estimand_and_analysis_registry.csv` |
| Simulation DGM/truth | B3-R `scenario_registry.json`, `truth_engine.py`, `truth_results.csv` |
| Simulation denominators | B3-R repaired interval/performance/failure CSVs |
| Empirical numbers | C2 public aggregate CSVs |
| Validation counts | clean/B1/B3-R/C1/C2 validation JSON/MD files |
| Manuscript authority | C6-FINAL fee-erratum `README.md`, handoff, erratum, manifests/checks |

## 18. Handoff change history and task mutation statement

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-07 | Initial standalone whole-repository handoff, independently reconciled against current code, contracts, results, validation evidence, archives, and dataset Git state. |

This task created `CHAVI_REPOSITORY_HANDOFF.md`. Per repository instructions, creation of a root file also requires regeneration of `PROJECT_ARCHITECTURE.md`; therefore the final task diff is expected to contain exactly those two documentation files. No scientific code, source data, frozen result, manifest, archive, experiment, dependency, or publication artifact was intentionally changed.
