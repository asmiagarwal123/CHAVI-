# CHAVI Step 2 review report

Dataset: `ds007116` snapshot `1.0.6`; expected commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`.  
Dataset checkout observed at commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`, tag/description `1.0.6`, status `## main...origin/main`.

## Scope and guardrails

This is a definition-and-feasibility draft. The 41 previously staged phenotype payloads were reused; no data were redownloaded. No raw data or pinned checkout content was modified. No final scores, composites, age adjustment, latent-factor model, ICC, SEM, MDC, prediction, dashboard, or report/caution/refuse threshold was calculated.

## Confirmed corrections

- Scientific score coverage excludes `participant_id` and `session_id`; identifiers remain in the variable specification and general inventories.
- Each QC inventory row is unique by source table, QC variable, and observed code; frequencies are recomputed directly from raw values. Unknown codes are not duplicated or summed across loops.
- Outcome coverage is score-specific for `eswan_adhd_inattention_total`, `eswan_adhd_total_score`, `mapssr_total_score`, `im_average`, and `em_average`; row counts and non-missing score counts are distinct.
- Undocumented-category checks are restricted to fields with an applicable categorical schema. Numeric fields report observed ranges and retain "expected range not documented locally" where appropriate.
- Cognitive repeat coverage is restricted to the 21 cognitive tasks and reports score-based counts separately from table-row/session availability.
- Missing tokens, documented unknown responses, and structural not-applicability are not collapsed. `n/a` is recorded as a raw missing token, not inferred to be structural.
- The Age Differentiation `cnb_adt_cnt_200` conflict is preserved: count-under-250-ms LongName versus `Units: ms`.

## Observed availability

- Verified payloads: **41/41**; parseable: **41**.
- Cognitive phenotype keys: **219**; participants: **131**; participants with 2+ observed cognitive sessions: **70**.
- Candidate score rows in `candidate_score_coverage.csv` are non-missing score observations; they are not approved usable-sample counts.
- Assessment mapping includes **225** participant/session rows. The documented `sub-20812` ses-2 continuation is not silently converted into a new CNB occasion.

## Supported candidate score definitions

The strongest draft support is for task accuracy-like outputs (`*_cr`, correct counts, sensitivity/proportion) as primary candidates and explicitly labelled RT fields as sensitivity alternatives. Penn CNB literature supports separating accuracy from speed; it does not justify collapsing every task to a single universal score. The official Penn update provides an additional definition for Digit Symbol `cnb_digsym_dscorrt`.

Reward/discounting measures remain outside the five cognitive domains. Their choices/preferences are not assigned a universal better/worse direction.

## Candidate domain mapping

`domain_mapping_draft.csv` records the proposed five-domain mapping and alternatives. Published CNB structure supports the broad Executive Control, Episodic Memory, Complex Cognition, and Social Cognition framework, with Sensorimotor Performance retained as a fifth CHAVI proposal. The mapping is not settled: PCET has a published complex-cognition caution, Digit Symbol and Trails have processing-speed ambiguity, and the combined AIM task does not establish separable constructs.

## QC and occasion definitions still unresolved

Observed QC code frequencies and documented meanings are in `qc_rules_draft.csv`. Provisional scenarios are descriptive only: V-only, V-or-F, no explicit N/X/S, and unresolved-QC. `VC` was observed in **13** QC code rows in the regenerated inventory; it is not assumed to mean valid. The exact scope of every code, the interpretation of F, 0, C, and VC, and treatment of missing QC remain for scientific review.

The occasion mapping preserves participant/session IDs and uses session `age` and anonymized/rounded `acq_time` when available. A session label is not proof of exact cognitive-assessment timing. Task version, administration condition, scan timing versus phenotype timing, and cross-visit comparability remain unresolved.

## Feasibility scenarios

The complete scenario tables are `eligibility_scenarios.csv`, `candidate_score_coverage.csv`, `candidate_domain_coverage.csv`, and `candidate_profile_coverage.csv`. Example strictness comparison for the one-primary-task-per-domain candidate profile:

- Unfiltered observed: **209 keys / 125 participants**.
- QC V-only: **193 keys / 118 participants**.
- QC V-or-F: **194 keys / 118 participants**.
- No explicit invalid codes: **207 keys / 125 participants**.
- Unresolved-QC only: **12 keys / 10 participants**.

These counts show how definitions change feasibility; they do not select a rule or establish reliability.

## Outcomes

`outcome_score_coverage.csv` reports non-missing score counts separately for each requested outcome. It distinguishes same-visit cognitive/outcome availability from participant-level baseline-cognitive plus later-outcome availability, and includes the stricter baseline-outcome requirement. No associations were run.

## Statistical analysis plan readiness

Evidence is sufficient to draft a statistical analysis plan skeleton, not a final plan. Scientific review is required before freezing primary variables, QC masks, occasion mapping, domain membership, missingness handling, direction alignment, age adjustment, weighting, or longitudinal estimands.

## Tests and reproduction

Synthetic Step 2 regression tests: **passed** (identifier excluded from scientific score class; unique QC source/variable/code key; unknown QC code retained as unresolved; n/a not inferred as structural missingness). Fixtures are temporary and not retained.

```powershell
python .\chavi_audit_ds007116_step2_20260907\audit_v3.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step2_20260907 --fixture-only
python .\chavi_audit_ds007116_step2_20260907\audit_v3.py --dataset .\ds007116 --phenotype-stage .\chavi_step1b_phenotype_staging_20260907 --output .\chavi_audit_ds007116_step2_20260907
```

Primary/local evidence is registered in `evidence_register.csv`. Key sources: [Gur et al. 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2832711/), [Moore et al. 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4345134/), [Penn CNB official updates](https://webcnp.med.upenn.edu/updates.html), [PennLINC cognitive mapping repository](https://github.com/PennLINC/transdiagnostic_executive_function/blob/main/cognitive/CNB_transformation_script_EF.Rmd), and the [official ds007116 snapshot release](https://github.com/OpenNeuroDatasets/ds007116/releases/tag/1.0.6).
