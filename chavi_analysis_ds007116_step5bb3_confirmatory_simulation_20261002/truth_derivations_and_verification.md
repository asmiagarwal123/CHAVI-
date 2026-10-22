# Truth derivations and verification

The target is the common target-pair distribution transformed by population baseline reference centers and scales. For `L_t=mean(Z_t)` and `q_t=Z_t-L_t 1`, the endpoints are the population ICC(A,1) limit `2 Cov(L1,L2)/(Var(L1)+Var(L2)+(E[L2]-E[L1])^2)`, `E[L2-L1]`, and `sqrt(E[||q2-q1||²]/5)`.

A common center cancels from both change endpoints; scale remains a nuisance transformation. Fold-specific center estimation can affect level ICC because it changes between-identity level variation.

S1–S4 use the stated Gaussian level/shape/noise DGM. S5 rounds every raw score to the nearest integer with NumPy ties-to-even. Its two visits have identical marginal distributions, so the population mean level change is exactly zero by symmetry; the B2 small numerical value was Monte Carlo error, not the target. S6 retains each deviation with probability 0.4 and otherwise sets it to `mu`, giving a 0.6 point mass and zero population MAD; S6/MAD is therefore structurally undefined, while S6/SD remains defined.

Truth rows are retained in `truth_results.csv`, with the exact S5 mean-change correction and numerical convergence metadata for non-analytic quantities.
