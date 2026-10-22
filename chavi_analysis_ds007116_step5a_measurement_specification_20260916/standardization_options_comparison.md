# Standardization options comparison (draft)

| Option | Definition | Advantages | Risks/requirements | Step 5A position |
|---|---|---|---|---|
| A. No age adjustment | retain raw task fields in task-native units | transparent; no model leakage; preserves observed meaning | different task scales and developmental age effects prevent a cross-task vector until a scale decision is approved | simplest reference/sensitivity; not a final profile score |
| B. Baseline-reference age adjustment | fit task-wise age model in a reference set using baseline observations; participant-grouped cross-fitting; apply frozen transformation to both occasions | preserves a baseline reference and avoids using follow-up to train the transform | reference definition, group/sex handling, nonlinear support, extrapolation, and cross-fitting must be approved | candidate primary only after human approval |
| C. Grouped all-occasion age adjustment | fit task-wise age model using all eligible occasions but keep participants grouped in resampling/fitting | more observations; can support flexible curves | follow-up contributes to transformation; optimistic leakage risk if not grouped; time and age are coupled | sensitivity only unless leakage controls and estimand are approved |

No option was executed. The next step must decide whether a common standardized coordinate is scientifically warranted, whether norms are external or internal, and whether the score direction is established for every task. If a simple model is adequate, prefer it over an unsupported nonlinear model.
