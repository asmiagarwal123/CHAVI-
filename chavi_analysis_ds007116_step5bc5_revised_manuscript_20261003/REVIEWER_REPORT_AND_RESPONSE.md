# Statistical methods reviewer report and response

## Strengths

1. Repaired simulation outputs, frozen contracts, independent C2 validation, and public aggregate reporting are unusually strong reproducibility assets.
2. The manuscript distinguishes coverage conditional on availability from available-and-covered probability.
3. C4 appropriately bounded causal, clinical, normative, and task-equivalence interpretations.

## Major issues and disposition

1. **Over-attribution risk in P2/P3.** C4's statement that P3 includes more of the workflow can be read as isolating estimated-reference uncertainty. A reviewer would object because P2/P3 also differ in resampling/refitting design and failure exposure. Source: B3-R corrected/confirmatory contracts. **Revision:** the revised manuscript says P2/P3 compare complete resampling procedures, not a variance decomposition.

2. **Selective emphasis on RMS.** C4 foregrounded RMS S1/S5 without equivalent ICC and mean-change confirmatory reporting. Source: B3-R confirmatory performance summary. **Revision:** a compact all-endpoint supplementary table is added; conclusions are endpoint- and mechanism-specific.

3. **P1 under-interpreted.** Subnominal P1 coverage means P2/P3 contrasts cannot all be attributed to refitting. Source: B3-R confirmatory performance summary. **Revision:** supplement states that P1 is oracle-conditional and records finite-sample/interval-construction limitations beyond reference refitting.

4. **Methods not fully reproducible on paper.** C4 omitted gates, no-redraw, linkage, random streams, and support/fallback behavior. Source: C1/C2/B3-R contracts. **Revision:** technical supplement added.

5. **Novelty claim too strong for a general methods paper.** Prior work already covers profile facets, ICCs, bootstrap intervals, cross-fitting, discrete bootstrap behavior, and simulation reporting. **Revision:** route narrowed to an applied/reproducibility paper with simulation support.

## Minor issues

6. Earlier/later language may imply common elapsed time. **Revision:** repository-defined occasion ordering is retained and elapsed time remains bounded.
7. LNB/CTAP metadata are incomplete. **Revision:** field-specific wording retained.
8. Published descriptor status. **Revision:** the 2026 Scientific Data article remains the reference.

## Open issue

No new experiment is required for the narrowed applied/reproducibility route. A metadata-informed new simulation would be required only for a claim of general calibration for Penn LEAD-like score mechanisms; no such claim is made.

