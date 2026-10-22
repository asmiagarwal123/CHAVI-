# Reference Cohort Recommendation

## Comparison Summary

| Property | Ref A (N=109) | Ref B (N=52) |
|---|---|---|
| Participants | 109 (all with >=1 complete occasion) | 52 (only those with >=2 occasions) |
| Age range | 8.69–16.75 | 8.80–16.18 |
| Age mean (SD) | 12.65 (2.05) | 12.64 (2.02) |
| Age mean difference t-test | p=0.952 |  |
| Observations (all 5 tasks) | 545 | 260 |

## Selection-bias analysis for Ref B

Reference B conditions on participants having **two complete synchronized V/F occasions**.
This is exactly the same condition used to select the longitudinal primary cohort.

### Implications:
1. Participants who dropped out after one occasion are EXCLUDED from Ref B.
2. Participants with more complete data tend to have higher engagement, possibly
   systematically better compliance, or lower task difficulty at baseline.
3. The internal reference parameters (mean, SD/MAD) would be estimated from a
   sample that has already been selected for longitudinal completeness.
4. This introduces **selection conditioning bias**: the reference statistics
   would reflect scores of participants with repeated data, not a broader internal sample.

### Why this matters:
If we standardize a participant's score relative to Ref B, we are implicitly
comparing them to a group that was pre-selected for being able to complete all
tasks at two timepoints. That is not a neutral internal reference.

## Recommendation: **Reference A (N=109)**

Reference A uses all 109 participants with at least one complete synchronized occasion.
It includes participants who only attended one timepoint, providing a broader and
less-selected internal reference.

**Advantages of Ref A:**
- Broader age coverage (more unique ages)
- No selection on follow-up completeness
- More training observations (545 vs 260 rows total)
- Less conditioning bias

**Leakage check:**
Reference A uses only the EARLIEST eligible occasion per participant.
No follow-up occasions are included. There is no temporal leakage.

**Recommendation is STRONG** — Ref A is scientifically preferred.
Ref B remains as a sensitivity option.

## Caveat
Neither reference is a normative sample. Both are internal references derived
from the same study dataset. Results must not be interpreted as population z-scores.
