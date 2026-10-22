# C6-FINAL requirement-to-evidence checklist

| Requirement | Status | Exact evidence / observed result |
|---|---|---|
| Correct RMS ratio | PASS | C2 `primary_bootstrap_intervals.csv`; `(1.3717392219336024-0.8007996882411338)/(1.1978314626167037-0.8105956091766748)=1.4743973953354241`; manuscript rounding remains 47.4% wider. |
| Other derived C2 widths | PASS | `validation/checks.json`: six unrounded P2/P3 percentile widths recomputed from C2 bounds. |
| Citation sets reconcile | PASS | `CITATION_VERIFICATION.md`; manuscript, References, and `references.bib` each contain the same nine works; no BibTeX-only entry. |
| Bibliographic record fields checked | PASS | DOI/publisher links in `CITATION_VERIFICATION.md`, accessed 2026-10-03. |
| Three real journal routes and fees/funding | PASS | `JOURNAL_FIT_COMPARISON.md`; PLOS ONE US$2,382; BMJ Open GBP 2,535; BMC current APC deliberately marked not verified. |
| Faculty handoff | PASS | `FACULTY_REVIEW_HANDOFF.md`; asks for judgment and states author-controlled decisions. |
| Manuscript, supplement, tables, figures, captions, plotting data | PASS | Package root, `tables/`, `figures/CAPTIONS.md`, `figures/*_data.csv`. |
| S1/S5 confirmatory simulation claims | PASS | B3-R `confirmatory_performance_summary_repaired.csv`; checked rows in `validation/checks.json`. |
| Privacy | PASS | `validation/checks.json`: public text/CSV/JSON/Bib identifier-pattern scan returned no matches. |
| Source preservation, manifests, ZIP integrity | PASS | `input_manifest.csv`, `output_manifest.csv`, `validation/checks.json`, ZIP SHA-256 sidecar. |
| DOCX/PDF convenience output | BLOCKED (nonessential) | No dependable render-and-verify workflow; Markdown faculty package is complete. |

All essential C6-FINAL items are PASS. Author-controlled submission decisions remain open and are not treated as package failures.
