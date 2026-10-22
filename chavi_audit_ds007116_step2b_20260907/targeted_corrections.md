# Targeted Step 2B corrections

1. The prior ‘one primary task score per candidate domain’ label is corrected to `at_least_one_candidate_task_per_domain_identity_may_differ`: it is a domain-wise union and does not imply a fixed task profile.
2. The five-domain intersection is now an explicit five-task intersection. Discounting tasks remain in a separate `all_21_cognitive_task_inventory_not_profile` inventory and cannot change the five-domain denominator.
3. Baseline ‘any cognitive score’ and ‘baseline complete fixed profile’ are separate outcome denominators.
4. Missing QC, partially missing QC, no QC field, conditional/no-automatic-validation codes, and unknown codes are retained as explicit unresolved QC states for sensitivity accounting.
5. Scientific meaning is driven by reviewed task/field entries, not `er`/`tp`/`tn` substring heuristics.

The corrected audit remains feasibility/specification work only. It does not create composites, reliability estimates, age-adjusted scores, predictions, classifiers, clustering, dashboards, or an Evidence Engine.

The fixed profile is a transparent feasibility proxy selected for broad domain coverage and parsimonious task identity: LNB, Face Memory, Matrix Reasoning, Emotion Recognition, and dominant-hand Finger Tapping. It is not a final CHAVI score.
