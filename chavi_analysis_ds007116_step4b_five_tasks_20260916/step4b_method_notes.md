# CHAVI Step 4B method notes

## Frozen scope

The five prespecified fields are Letter N-back `cnb_lnb_mcr`, Face Memory `cnb_cpf_cr`, Matrix Reasoning `cnb_pmat_cr`, Emotion Recognition `cnb_er40_cr`, and Dominant Finger Tapping `cnb_ctap_dom`. The source is the local verified Step 1B payload corresponding to Penn LEAD ds007116 snapshot 1.0.6 at commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`.

## Eligibility and pairing

All raw rows are counted before filtering. A score is eligible only when finite, its QC code is exactly `V` or `F`, its session label is `ses-<integer>`, and the Step 3B occasion is not marked as a continuation without a new CNB occasion. Invalid/skipped/excluded QC takes precedence as the row-level exclusion reason when score missingness is also present. The first two eligible observations per participant are selected in strict numeric session order. Nonpositive nominal intervals are rejected. Participants contribute at most one pair per task.

## Statistics

ICC(A,1) is two-way random-effects absolute agreement, single measure, with the documented ANOVA formula `(MS_R - MS_E) / (MS_R + (k-1)MS_E + k*(MS_C-MS_E)/n)` for `k=2`. ICC(C,1), Pearson, Spearman, later-minus-earlier mean change, and descriptive Bland-Altman limits of agreement are sensitivities/descriptives. Negative estimates are retained and no arbitrary reliability categories are used.

## Bootstrap

Each task uses 5000 resamples of n participant pairs with replacement and seed 20260914. The participant pair is the resampling unit. Repeated sampled participants remain repeated bootstrap copies and are not collapsed. Percentile intervals use linear interpolation at 2.5% and 97.5%.

## Missingness and timing correction

Missing earlier and later score counts are computed from the first two source observations per participant before complete-pair filtering. Structural absence of a later candidate slot is reported separately. Timing is derived from rounded/anonymized acquisition metadata only when available and positive; it is not presented as exact cognitive-assessment timing.

## Reproduction and integrity

Face Memory is compared against the independent Step 4A-R statistical crosscheck in `face_memory_reproduction_check.csv`. Input hashes, dataset Git state, and prior Step 4A/Step 4A-R directory hashes are in `step4b_provenance.json`. The new output directory is the only directory written by this script.
