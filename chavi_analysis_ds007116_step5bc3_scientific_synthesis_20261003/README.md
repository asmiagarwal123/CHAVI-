# Step 5B-C3 scientific synthesis package

This package integrates frozen Step 5B-A/B1/B3-R/C1/C2 evidence. It does not create new estimands, rerun bootstrap draws, add simulation scenarios, or modify upstream artifacts.

## Main decision

Proceed to manuscript drafting as a bounded methodological–reproducibility paper with an empirical sensitivity illustration. The defensible center is a failure-aware comparison of fixed versus jointly refitted reference transformations for longitudinal five-task profile summaries. Do not claim universal calibration, clinical change, normative generalizability, causal age effects, or a new invention of cross-fitting, MAD, ICC, bootstrap refitting, profile decomposition, or ADEMP.

The single recommended next action is a focused measurement-documentation resolution: obtain authoritative definitions for LNB denominator/load and CTAP units/aggregation and document task-version comparability and visit timing. If those cannot be resolved, manuscript wording must remain explicitly score-field-specific and occasion-based.

## Contents

- `SCIENTIFIC_SYNTHESIS_AND_PUBLICATION_DECISION.md`: integrated assessment and recommendation.
- `PLAIN_LANGUAGE_PROJECT_EXPLANATION.md`: nontechnical explanation.
- `FINAL_SCOPE_AND_RESEARCH_QUESTION.md`: frozen manuscript scope and claim boundary.
- `aggregate_tables/`: public aggregate evidence copied or deterministically derived from frozen sources.
- `figures/`: three figures in SVG/PDF/PNG, captions, and plotting data.
- `literature_search_log.csv`, `closest_work_matrix.csv`, `references.bib`: targeted-search record.
- `claim_evidence_matrix.csv`: claim-level provenance and permitted wording.
- `input_manifest.csv`, `artifact_manifest.csv`: provenance and output integrity.
- `validation/synthesis_checks.json`: automated checks; scientific judgments remain in the reports.
- `code/build_synthesis.py`: standard-library builder. Run from the project root with `.\.venv\Scripts\python.exe ...\code\build_synthesis.py`.

Public outputs contain counts and aggregates only. Participant-linked C2 audit files were used only to verify identity-manifest counts and are not copied here.

