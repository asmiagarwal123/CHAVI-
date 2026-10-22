# C3 publication status correction

## Correction

The C3 package described the Penn LEAD descriptor as a 2025 preprint. That statement is outdated. The primary journal record is Sevchik BL, Shafiei G, Murtha K, et al., *A longitudinal data resource to study brain development and transdiagnostic variation in executive function*, **Scientific Data**, published 20 August 2026, DOI: 10.1038/s41597-026-08095-1. The journal page identifies it as a Scientific Data data descriptor, gives the received and accepted dates, and supplies a permanent DOI. It is therefore cited in C4 as a peer-reviewed journal article, not as a preprint.

## C3 records affected

| C3 record or claim | Effect | C4 handling |
|---|---|---|
| `SCIENTIFIC_SYNTHESIS_AND_PUBLICATION_DECISION.md`: “2025 preprint, not peer-reviewed” | Materially incorrect status | Replaced with the 2026 Scientific Data citation and publication status. |
| `PLAIN_LANGUAGE_PROJECT_EXPLANATION.md`: descriptor described as preprint | Status error | Manuscript uses journal descriptor. |
| `FINAL_SCOPE_AND_RESEARCH_QUESTION.md`: descriptor reference | Outdated bibliographic record | Corrected reference only; claim boundaries unchanged. |
| `literature_search_log.csv` and `closest_work_matrix.csv` | Citation/status and uncertainty entry outdated | C4 records the journal descriptor and retains the dataset-version/field-definition uncertainty. |
| `references.bib` entry `sevchik2025pennlead` | Wrong work/year/status for manuscript use | Replaced by `sevchik2026pennlead`. |

## Published descriptor compared with the earlier preprint and local ds007116 material

The published title changes from the preprint title and is now journal published. Both records describe a Penn LEAD resource of 132 participants and 225 imaging sessions, repeated cognitive testing, multimodal imaging, OpenNeuro availability, and detailed quality-control material. The published descriptor is authoritative for those resource-level statements.

Neither the accessible journal record nor the local BIDS JSON sidecars directly establishes every CHAVI-specific measurement property. The local release used by CHAVI is labelled `ds007116`, whereas the earlier accessible preprint text referred to raw accession `ds006688`; the published descriptor must not be treated as proof that these identifiers denote an identical frozen release without a versioned accession crosswalk. Most importantly, resource-level task descriptions do not establish `cnb_ctap_dom` units/trial filter, LNB occasion-specific denominator/load composition, or scoring-rule equivalence. C4 therefore uses the published descriptor for citation and resource context, and local field metadata for field-specific wording.

No protected C3 file was modified.

