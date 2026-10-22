# CHAVI measurement evidence dossier

## Five proxy scores

- LNB `cnb_lnb_mcr`: released true-positive count for 1-/2-back. The denominator/load mapping is unresolved; do not call it percent correct or transform it using an invented denominator.
- Face Memory `cnb_cpf_cr`: face-memory correct-count output. Public CNB documentation supports target/foil recognition; historical false-alarm treatment and exact LEAD version remain unknown.
- Matrix Reasoning `cnb_pmat_cr`: matrix-reasoning correct-count output. The documented stopping rule prevents assuming a fixed denominator.
- ER40 `cnb_er40_cr`: emotion-recognition correct-count output; the public task page documents 40 faces, while historical conditions/QC scope remain uncertain.
- Dominant CTAP `cnb_ctap_dom`: released mean dominant-hand trial summary. Public documentation supports 10-second trials/five per hand; the exact count/rate aggregation must still be frozen.

These support narrow released-score audits. They do not support longitudinal equivalence, equal latent contribution, or a validated broad-domain composite.

## Mapping resolution and alternatives

Digit Symbol `cnb_digsym_dscor` is consistently assigned to Executive control/processing speed in the current executable candidate-domain configuration because the pinned public CNB task documentation lists it with Executive Control processing-speed tasks. Its earlier Complex-cognition placement is preserved as historical Step 2 mapping only. The 2024 Digit Symbol RT update is not assumed to rewrite the historical LEAD field. PCET remains a complex-cognition alternative based on primary factor evidence; AIM is a combined-construct candidate; Trails remain task-level speed candidates.

## QC and sources

Released dictionary meanings are preserved exactly: V Valid; F Likely valid with a limited-response problem; 0 No autovalidation rule available; S Skipped; N Not Valid; C Assessor Comment; X Excluded. Missing/partial/no-applicable QC remain unresolved. Sources: [Penn CNB task documentation](https://webcnp.med.upenn.edu/explore-tests.html), [Penn CNB manual](https://webcnp.med.upenn.edu/manual.html), [Penn CNB updates](https://webcnp.med.upenn.edu/updates.html), [Gur et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC2832711/), [Moore et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC4345134/), and [PennLINC mapping](https://github.com/PennLINC/transdiagnostic_executive_function/blob/main/cognitive/CNB_transformation_script_EF.Rmd).
