# C6 requirement-to-evidence checklist

| Requirement / manuscript claim | Status | Exact evidence |
|---|---|---|
| Faculty-review manuscript | PASS | `CHAVI_FACULTY_REVIEW_MANUSCRIPT.md` |
| Reproducibility supplement | PASS | `METHODS_AND_REPRODUCIBILITY_SUPPLEMENT.md` |
| Tables, figures, captions, plotting data are self-contained | PASS | `tables/`; `figures/CAPTIONS.md`; `figures/*_data.csv` |
| Bibliography and citations | PASS | `references.bib`; manuscript References section; `CITATION_VERIFICATION.md` |
| Journal-route comparison using primary publisher records | PASS | `JOURNAL_FIT_COMPARISON.md` (official URLs, checked 2026-10-03) |
| Author decisions explicitly separated | PASS | `AUTHOR_DECISIONS_NEEDED.md` |
| Plain-language brief and C5-C6 change record | PASS | `PLAIN_LANGUAGE_FACULTY_BRIEF.md`; `C5_TO_C6_CHANGES.md` |
| Title: failure-aware resampling evaluation | PASS | Manuscript title; defined failure/availability rules in supplement; B3-R contract and `tables/simulation_failure_reason_summary.csv` |
| Abstract: S1 P2/P3 RMS coverage 0.803/0.9175 | PASS | B3-R `confirmatory_performance_summary_repaired.csv`, S1/P2,P3/MAD/RMS/percentile rows |
| Abstract: S5 P2 availability 0.997 and P3 0.630/available-covered 0.6025 | PASS | Same B3-R file, S5/P2,P3/MAD/RMS/percentile rows |
| Abstract: primary n=52 and point estimates | PASS | C2 `endpoint_estimates.csv`, primary M0/MAD rows; C6 `tables/empirical_all_planned_point_estimates.csv` |
| Abstract/Results: P3 RMS interval 47.4% wider | PASS | C2 `primary_bootstrap_intervals.csv`; unrounded width ratio 1.4744187226602014 in `validation/checks.json` |
| Results: all 12 primary interval values | PASS | C2 `primary_bootstrap_intervals.csv`; C6 `tables/empirical_primary_intervals.csv`; manuscript Table 2 |
| Results: all 18 planned point estimates | PASS | C2 `endpoint_estimates.csv`; C6 `tables/empirical_all_planned_point_estimates.csv`; manuscript Table 1 |
| Results: confirmatory pilot distinction | PASS | B3-R contract and manuscript Methods/Results; only S1/S5 called confirmatory |
| Results: coverage reported with availability | PASS | Manuscript abstract, Methods, Results Table 3; B3-R performance summary |
| Conclusion: no universal calibration/superiority | PASS | B3-R S1/S5 rows, manuscript Conclusion/Discussion wording |
| Conclusion: no causal development/clinical/reliability/task-equivalence claim | PASS | Manuscript Conclusion/Discussion; data limitations documented in C2/C1 and NDA dictionary citation |
| Frozen formula/population/folds/truth/resampling rules | PASS | C1/B3-R contracts; supplement sections 1-2 |
| No participant identifiers in public outputs | PASS | `validation/checks.json`: regex scan of all C6 text/CSV/JSON/Bib outputs |
| Archive integrity, manifests, hashes, upstream preservation | PASS | `validation/checks.json`, `input_manifest.csv`, `output_manifest.csv`, ZIP SHA-256 sidecar |
| DOCX/PDF manuscript | BLOCKED | Omitted deliberately: no dependable document-rendering/verification runtime was available; Markdown package is reviewable. |

Essential scientific and package items are PASS. The DOCX/PDF convenience artifact is nonessential and BLOCKED; author-controlled submission decisions remain open in `AUTHOR_DECISIONS_NEEDED.md`.
