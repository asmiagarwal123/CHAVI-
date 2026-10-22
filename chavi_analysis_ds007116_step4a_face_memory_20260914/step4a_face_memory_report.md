# CHAVI Step 4A empirical result: Penn Face Memory

## Outcome

Step 4A produced the first empirical CHAVI longitudinal-agreement result using the raw Penn Face Memory released correct-response/count-like field `cnb_cpf_cr`. The analysis uses a task-specific cohort and does not require the complete five-task profile.

The result describes agreement of the released score field across the observed eligible Penn LEAD follow-up occasions. It is not a diagnosis, intelligence measure, validated broad cognitive domain, permanent memory-strength statement, pure test-retest error estimate, developmental estimate, practice-effect estimate, or clinical-validity result.

## 1. What was measured

- Source table: `phenotype/penn_face_memory_test.tsv`.
- Exact field: `cnb_cpf_cr`.
- Local dictionary definition: `CPF Total Correct Responses`.
- Primary QC: exact local code `V` (Valid) or `F` (Likely valid with a limited-response problem).
- Pairing: first two eligible Face Memory observations per participant in nominal numeric session order.
- Included independent participants: **59**.
- Candidate participants: **131**.
- Excluded candidate participants: **72**.

The official Penn CNB documentation describes the Penn Face Memory Test as an episodic-memory task presenting 20 faces mixed with 20 foils, with an approximately 3.5-minute task duration ([official Penn CNB task documentation](https://webcnp.med.upenn.edu/explore-tests.html)). The local dictionary does not document units, a possible score range, or a score-direction label.

## 2. What was found

### Raw score summaries

| Occasion | N | Mean | SD | Median | IQR | Minimum | Maximum | Missing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Earlier eligible observation | 59 | 31.3729 | 4.3940 | 32.0000 | 7.0000 | 22.0000 | 40.0000 | 0 |
| Later eligible observation | 59 | 32.2203 | 5.6935 | 33.0000 | 9.5000 | 19.0000 | 40.0000 | 0 |

Observed paired change is defined as **later minus earlier**. Mean change was **0.8475** (SD 4.7482); median change was **1.0000** (IQR 4.5000), with a minimum of -9.0000 and maximum of 12.0000. 33 participants (55.9%) increased, 9 (15.3%) were unchanged, and 17 (28.8%) decreased.

The participant-bootstrap 95% percentile interval for the mean paired difference was **[-0.3729, 2.0343]**, based on 5000 successful replicates and 0 failed/undefined replicates.

### Agreement and sensitivity estimates

| Statistic | Estimate | Bootstrap 95% percentile interval | Status |
|---|---:|---:|---|
| Primary ICC(A,1), absolute agreement, single measure | 0.560473 | [0.343745, 0.718958] | ok |
| ICC(C,1), consistency, single measure | 0.564114 | [0.354098, 0.723349] | ok |
| Pearson correlation | 0.583156 | [0.370071, 0.747053] | ok |
| Spearman correlation | 0.555388 | [0.323822, 0.734639] | ok |

The primary ICC is the untruncated raw estimate. Its formula and convention are recorded in `step4a_analysis_contract.json` and `step4a_method_notes.md`. Correlations should not be read as evidence of absolute agreement: a correlation can remain high despite a systematic occasion shift.

### Exclusions and accounting

The exact participant accounting is in `face_memory_candidate_accounting.csv`, with excluded participants in `face_memory_exclusions.csv`. The partition is:

| Category | Count |
|---|---:|
| Candidate participants | 131 |
| Included primary pairs | 59 |
| Excluded participants | 72 |

The inclusion and exclusion counts reconcile exactly. The Step 3B-to-Step 4A row trace contains 219 Face Memory source rows; changed eligibility rows: 0.

## 3. What the result may support

Within this pinned Penn LEAD snapshot and this documented-valid/likely-valid task-specific cohort, the released `cnb_cpf_cr` score showed the reported degree of longitudinal absolute agreement across the recorded first-two eligible occasions. The result can be used as a transparent measurement-foundation result and as a reason to inspect score discreteness, occasion shifts, and uncertainty before considering any broader profile statement.

## 4. What cannot be concluded

- The result does not establish pure measurement error because the follow-up intervals are long and development, practice, state change, and measurement noise are not separated.
- It does not establish unchanged Penn Face Memory instrument/version equivalence. The available metadata support comparison by session label only; exact version and administration equivalence remain unresolved.
- It does not validate a broad episodic-memory or general-cognition composite.
- It does not measure intelligence or a permanent individual memory trait.
- It does not establish diagnostic, clinical, educational, or treatment utility.
- It does not justify an ICC threshold as a CHAVI reporting rule.
- It does not support SEM/MDC, age adjustment, standardization, imputation, prediction, profile selection, or Report/Caution/Refuse decisions.

## Reproducibility and provenance

The repository was checked before and after the analysis and remained at the pinned commit with no tracked changes. The exact input paths and SHA-256 hashes, output hashes, code hash, contract hash, figure hashes, focused tests, and software version are in `step4a_provenance.json`.

Primary numerical sources:

- `face_memory_descriptive_results.csv`
- `face_memory_agreement_results.csv`
- `face_memory_bootstrap_results.csv`
- `face_memory_included_pairs.csv`
- `face_memory_candidate_accounting.csv`

Figures are reproducible from `face_memory_included_pairs.csv` by running `step4a_face_memory.py`.
