# Methods and reproducibility supplement

## Population, transformation, and estimands

Reference A has 109 participants: 52 paired targets and 57 auxiliaries. Design B uses target folds 11/11/10/10/10 and fitting counts 98/98/99/99/99. The primary M0/MAD analysis has 52 pairs; M0/SD has 52; matched M0/M1 support has the same 42; fixed strict-V has 41; reselected strict-V has 45. These are distinct estimand populations.

Fields are `cnb_lnb_mcr`, `cnb_cpf_cr`, `cnb_pmat_cr`, `cnb_er40_cr`, and `cnb_ctap_dom`, all direction +1. M0 is `(y-mean(reference training y))/s`; MAD is `median(abs(y-median(y)))/0.6744897501960817`; SD uses `ddof=1`. M1 is used only under frozen age support; unsupported/undefined scales retain their contract-defined status, not an invented replacement.

`L_it=sum_j z_ijt/5`, `q_ijt=z_ijt-L_it`, mean change is `mean_i(L_i2-L_i1)`, and RMS is `sqrt(sum_i sum_j(q_ij2-q_ij1)^2/(5n))`. ICC(A,1) is `(MSR-MSE)/(MSR+(k-1)MSE+k(MSC-MSE)/n)` with `k=2`. Profile correlation is descriptive and follows the frozen near-zero-norm rule.

## Simulations and resampling

All simulation datasets use 52 targets, 57 auxiliaries, and frozen folds. Task means are `(10,12,14,16,18)`; level variance is 0.5; four Helmert shape coordinates have covariance `0.5 I`; noise covariance is `0.5 C` with `C_jk=0.3^|j-k|`. S1 has 0.8 level/shape correlation; S2 has 0.8 level and zero shape correlation; S3 adds common +0.5; S4 adds +0.5 Helmert-1 shift; S5 rounds nearest integer ties-to-even; S6 fixes deviations at zero with probability 0.6 (MAD structurally undefined) and otherwise retains them with probability 0.4. Truth follows the frozen data-generating policy; S6/MAD is undefined and S5 mean-change truth is zero.

The pilot has 100 outer datasets in S1-S6; confirmatory has 2,000 in S1/S5. Each procedure uses 999 attempts, requires at least 950 valid and `floor(0.025*n_valid)>=20`, finite point/defined truth, and has no redraw. Percentile/basic use linear tail quantiles. Conditional coverage denominator is available intervals; availability and available-and-covered denominators are attempted outer datasets. Stored paired differences are method A minus B with stored MCSE.

P1 is oracle conditional; P2 resamples target pairs while holding original transform/coordinates fixed; P3 resamples targets and auxiliary reference draw then refits; P4 refits with fold stratification. Target multiplicity is linked across analysis/reference, each target is held out of its own fold, one auxiliary draw is shared across folds, and unused folds are not fit. These are complete resampling-procedure comparisons, not isolation of a reference-uncertainty variance component.

## Empirical bootstrap

Empirical attempts are 999 with no redraw, minimum 950 valid, 20-tail gate, linear quantiles, PCG64DXSM, master seed 20261003, and SHA-256-derived streams. P2/P3 share target draws; P3 uses an auxiliary stream. Nonfinite coordinates invalidate coordinate endpoints; ICC degeneracy invalidates ICC only; reference-fit failure is retained as an ordinary invalid P3 endpoint draw. All 12 primary empirical cells had 999 valid draws; this is availability, not coverage.

