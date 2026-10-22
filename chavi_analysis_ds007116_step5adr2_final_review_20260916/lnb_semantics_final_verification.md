# LNB Score Semantics Final Verification

## Source
`ds007116/phenotype/short_letter_2back.json`

## Verified field: `cnb_lnb_mcr`
- **LongName (from JSON):** LNB True Positive Responses for 1-BACK and 2-BACK Trials
- **Units (from JSON):** NOT DOCUMENTED in JSON
- **Field type:** COUNT of true positive responses (NOT response time)

## Sibling RT field: `cnb_lnb_mrtc`
- **LongName:** LNB Median Response Time for True Positive responses for 1-BACK and 2-BACK response
- **Units:** ms
- **Implication:** The RT variable is a separate field with explicit `Units: ms`. `cnb_lnb_mcr` has no Units field and its LongName contains no "Response Time" — it is unambiguously the count field.

## Observed distribution
- N observed: 206
- Min: 6.0, Max: 20.0
- Mean: 17.63, Median: 18.0, SD: 2.70
- Values at ceiling (=20): 59 (28.6%)

## Direction
**POSITIVE** — higher count = more correct responses.

## Unresolved caveat
Maximum observed value is 20. Official Penn CNB page states 45 target trials across 0-, 1-, and 2-back. cnb_lnb_mcr covers only 1-back and 2-back trials. Exact denominator for 1-back + 2-back trials not confirmed in local JSON. Do NOT claim normalized accuracy.

## ICC applicability
Step 4B ICC(A,1)=0.660 was computed on the raw count field. Direction is positive. No reversal was applied then or now. ICC values remain numerically valid as reported.

## Conclusion
`cnb_lnb_mcr` is confirmed as a **true-positive response count**, not a response-time variable.
Direction multiplier = +1. No reversal applied or required.
D18 recommendation: **retain positive direction with open denominator caveat**.
