# Measurement specification review

## Decision-ready candidate specification

The draft fixed profile uses one explicit task/field per broad domain: LNB `cnb_lnb_mcr` (Executive control), Face Memory `cnb_cpf_cr` (Episodic memory), Matrix Reasoning `cnb_pmat_cr` (Complex cognition), Emotion Recognition `cnb_er40_cr` (Social cognition), and dominant-hand Finger Tapping `cnb_ctap_dom` (Sensorimotor performance). This is a feasibility proxy, not a final composite. The exact manifest is in `score_manifest_draft.csv`.

## Evidence and unresolved definitions

The Penn CNB Explore Tests page documents public task structure and durations: LNB has 0-/1-/2-back conditions; Digit Symbol is processing speed; memory tasks use target/foil recognition; PMAT has a stopping rule; ER40 has 40 faces; Finger Tapping uses 10-second trials. The CNB methods paper describes accuracy as number correct and speed as response time for correct answers. The factor paper separates accuracy and speed and reports PCET as a possible complex-cognition alternative. These sources support candidate construct labels, not equivalence between the online current CNB documentation and this historical Penn LEAD export.

ADT `cnb_adt_cnt_200` retains a count-versus-ms metadata conflict. LNB `cnb_lnb_mcr` has a local definition/range that does not establish a denominator or load mapping. CPT sensitivity is retained as sensitivity, not d-prime. Motor Praxis correct count and praxis RT are separate. Trails exact task/version and public definition remain gaps. The July 2024 Digit Symbol RT update is recorded as a version-sensitive issue.

## Sources

- [Penn CNB Explore Tests](https://webcnp.med.upenn.edu/explore-tests.html) (task structure, conditions, trial counts, duration).
- [Penn CNB manual](https://webcnp.med.upenn.edu/manual.html) (assessment types, sessions, incomplete batteries, raw data, motor-practice gateway).
- [Penn CNB updates](https://webcnp.med.upenn.edu/updates.html) (7 July 2024 Digit Symbol DSCORRT update).
- [Gur et al. 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2832711/) (accuracy/speed definitions).
- [Moore et al. 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4345134/) (factor/domain evidence).
- [PennLINC mapping](https://github.com/PennLINC/transdiagnostic_executive_function/blob/main/cognitive/CNB_transformation_script_EF.Rmd) and [cognitive README](https://github.com/PennLINC/transdiagnostic_executive_function/tree/main/cognitive) (variable mappings and sub-20812 continuation note).
