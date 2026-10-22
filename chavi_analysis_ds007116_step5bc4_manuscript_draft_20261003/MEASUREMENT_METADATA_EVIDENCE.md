# Measurement metadata evidence

The table distinguishes direct documentation from inference. It is intentionally limited to the four questions authorized for C4.

| Question | Authoritative locator | Supported answer | Unresolved part | Manuscript wording |
|---|---|---|---|---|
| `cnb_lnb_mcr`: count, denominator, loads, comparability | Local `ds007116/phenotype/short_letter_2back.json`, field `cnb_lnb_mcr`; NIMH Data Archive PennCNB01 dictionary, `cnb_lnb_mcr` | The field is “LNB True Positive Responses for 1-BACK and 2-BACK Trials.” The NDA dictionary gives integer range 0–20. Thus it aggregates correct targets from 1- and 2-back, excluding 0-back. | The local release lacks a field-level form/version variable and an occasion-specific count of trials by load. The dictionary lists possible LNB forms but does not prove which form was administered at each CHAVI occasion or establish equivalent denominator/load composition. | “Letter n-back true-positive responses for 1- and 2-back trials (`cnb_lnb_mcr`; documented range 0–20).” Do not call it an accuracy proportion or claim fixed denominators/equivalence. |
| `cnb_ctap_dom`: unit and dominant-hand aggregation | Local `ds007116/phenotype/short_computerized_finger_tapping_task.json`, `cnb_ctap_dom`; NIMH Data Archive PennCNB01 dictionary | The released field is “CTAP Mean of Dominant Hand Trials.” It is a floating-point field and is distinct from non-dominant, SD, total, and unfiltered fields. | Neither locator supplies the physical unit, trial duration, number of trials, filter rule, or arithmetic rule behind the mean. “Taps per second” is not documented for this released field. | “Mean of dominant-hand trials (`cnb_ctap_dom`; unit and trial aggregation not documented in the examined release metadata).” |
| Five task versions/scoring across occasions | Published descriptor: Sevchik et al. 2026, Scientific Data, DOI; local five task JSON sidecars | The descriptor documents repeated cognitive testing at longitudinal imaging visits. Local sidecars name the fields and validation codes. | No examined source provides a version-by-occasion crosswalk, item set, form, denominator, or scoring-rule equivalence for all five fields. Matching column names cannot establish equivalence. | “Repeated measurement occasions using the released score fields”; do not claim identical task versions or measurement equivalence. |
| Session order and elapsed time | Local sidecars: `session_id` “assigned chronologically via Flywheel created timestamp”; local README; earlier accessible descriptor’s Data Records text | Session labels establish chronological order by Flywheel-created timestamp. The release documentation warns about repeats/incomplete runs. The preprint Data Records text says imaging acquisition dates were anonymized/rounded; the local README says dates/times were rounded. | Exact elapsed time between the analyzed cognitive occasions and their relation to cognitive administration are not established by the session labels alone. | “Earlier versus later repository-defined cognitive occasion”; do not report an elapsed-time interval, developmental rate, or causal age effect. |

## Published descriptor record

The journal article was verified at the publisher’s primary record: Scientific Data, 20 August 2026, DOI `10.1038/s41597-026-08095-1`, with supplementary information linked by the journal. It documents the resource, phenotyping and QC context but, in accessible material, not the above CHAVI-field-level unresolved details.

## Optional unsent curator questions

1. For `cnb_lnb_mcr` in the ds007116 release, which 1- and 2-back forms and target counts apply at each session, and were they constant across repeated cognitive occasions?
2. For `cnb_ctap_dom`, what is the unit, trial duration/count, filtering rule, and exact aggregation used for the released mean?
3. Is there a version-by-occasion crosswalk for the five released score fields, including scoring-rule changes?
4. Which timestamp represents cognitive administration, and what de-identification/rounding affects interval calculations?

