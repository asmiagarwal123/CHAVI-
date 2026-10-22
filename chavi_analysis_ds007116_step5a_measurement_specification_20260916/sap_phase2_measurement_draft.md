# Draft SAP: Phase 2 measurement specification

**Status:** draft, not final and not preregistered.

**Research question.** Can the five exact CHAVI cognitive task measurements be placed into a defensible longitudinal measurement framework after confirming score semantics, synchronized occasions, age support, and error structure? This draft does not answer a clinical, diagnostic, prediction, or intervention question.

**Data and cohort.** Use the pinned ds007116 snapshot 1.0.6 and verified Step 1B payloads, with Step 3A/3B occasion/QC provenance and Step 4A/4A-R/4B/4B-R artifacts. Start from 132 registered participants. The candidate primary profile denominator is 52 participants with two first numeric-ordered same-session complete occasions under exact V/F for all five fields. Task-specific pair intersection is 53 and same-session task-pair alignment is 50; these are not interchangeable.

**Synchronized visit rule.** A visit is complete only if all five exact task fields are finite and raw QC is exactly V or F in the same repository session; continuation sessions are excluded. Preserve raw values, QC, task, and source-row provenance. No imputation.

**Score semantics and transformation.** Read local JSON dictionaries and official Penn CNB documentation. Do not infer undocumented theoretical ranges or reverse directions. Option A (raw) is a transparent candidate; Option B (baseline-reference, participant-grouped cross-fitted age adjustment) and Option C (grouped all-occasion adjustment) are candidates pending approval. No transformation is run here.

**Profile formulas.** If approved transformed coordinates exist later, define `Z_it`, elevation `L_it`, centered shape `S_it`, scatter `D_it`, shape RMSE, and descriptive shape correlation as in `profile_formula_registry.csv`. Do not compute final participant profile values in this step.

**Planned analyses.** Step 4B task-level agreement is complete. Future Phase 2 work may specify ICC(A,1), mean change, SEM/MDC, bootstrap, scatter and shape summaries, with the participant as bootstrap unit. Profile-level ICC, profile shape stability, and any individual-level reliability are prohibited in Step 5A.

**Multiple comparisons.** Treat task-level and profile-level summaries as separate estimand families. Any adjustment or estimation hierarchy requires supervisor approval; none is silently applied here.

**Extremes and claims.** Retain extreme raw changes and conduct influence diagnostics; do not automatically delete. Permitted claims are data provenance, score-field descriptions, synchronized-cohort counts, and measurement-specification proposals. Prohibited claims include prediction, clinical/diagnostic interpretation, threshold performance, individual classification, final reliability, and profile stability.

**Open decisions.** Approve score direction, age-adjustment option/reference, cross-fitting implementation, profile level/shape/scatter primary estimands, missing/extreme policies, scheduled-session sensitivity, treatment of the three task-misaligned participants, ipsative-risk analysis, and version uncertainty.
