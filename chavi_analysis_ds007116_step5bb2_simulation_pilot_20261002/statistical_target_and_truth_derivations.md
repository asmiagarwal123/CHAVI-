# Statistical targets and truth derivations

The target distribution is the stated target-pair DGM, transformed by common population baseline-reference task means `m` and scales `d`; it is not a realized cross-fitted estimate. Let `Z_t=D^{-1}(Y_t-m)`, `a=1/5`, `L_t=a'Z_t`, and `P=I-11'/5`.

For two measurements, the large-`n` ANOVA components are `MS_R -> (v1+v2+2c)/2`, `MS_E -> (v1+v2-2c)/2`, and `2 MS_C/n -> (mu2-mu1)^2`. Therefore ICC(A,1) tends to `2c/[v1+v2+(mu2-mu1)^2]`, not merely a latent correlation. Mean change is `a'D^{-1}E(Y2-Y1)`. RMS shape displacement is `sqrt({tr[P D^{-1}Var(Y2-Y1)D^{-1}] + ||P D^{-1}E(Y2-Y1)||^2}/5)`.

A common task-wise reference center cancels from `Z2-Z1`. At fixed scales, mean level change and centered-shape displacement are invariant to center perturbation. Scale remains in both; fold-specific centers need not cancel across different participants when computing between-person level ICC, so level ICC can change. Population MAD and SD are distinct nuisance scales.

Continuous marginal scores are Gaussian with covariance `0.5*11' + 0.5*HH' + 0.5*C`; every marginal variance is 1.4, so normal-consistent MAD and SD equal `sqrt(1.4)`. Cross-visit covariance is `0.5*rho_level*11' + 0.5*rho_shape*HH'`. S5 reference scales use the exact rounded-normal marginal probabilities and two independent 500,000-pair numerical batches for endpoint truth. In S6 the independent retention mask gives `P(Y=mu)=0.6`, hence median absolute deviation zero, while variance is `0.4*1.4>0`; MAD targets are structurally undefined and SD targets are valid. Independent numerical streams validate analytic truths.

P1 targets ordinary sampling under a known population transformation. P2 is evaluated against that same unconditional population target but freezes an estimated transformation within each bootstrap; this does not establish fully conditional validity under overlap. P3/P4 propagate their specified role-conditioned reference resampling. None reproduce recruitment, selection, or empirical missingness.
