# Draft cognitive score definitions

This is a proposal for scientific review, not a scoring implementation. It uses exact local table/column names. Primary candidates are chosen from documented accuracy-like outputs where available; RT/speed and alternate accuracy/error fields are sensitivity alternatives. No standardization or composite was computed.

## Draft rules

1. Keep one primary score per task for feasibility accounting; retain speed and accuracy separately until the speed-accuracy policy is approved.
2. Treat counts/proportions of correct responses as higher-is-plausibly-better, subject to task-specific validity and range review.
3. Treat response-time fields as lower raw time = faster, with direction reversal only as a proposed later alignment—not as a raw-data correction.
4. Keep reward/discounting outputs separate; do not call preferences better or worse.
5. Do not use item components, errors, form fields, QC/status fields, or derived outcome fields as cognitive performance scores unless explicitly approved.

## Domain proposal and alternatives

Executive Control: AIM `cnb_aim_aimtot`, PCET `cnb_pcet_cr`, LNB `cnb_lnb_mcr`, CPT `cnb_cptnl_total_sen`, Trails B `cnb_trails_rt`.  
Episodic Memory: Penn Word `cnb_cpw_cr`, Penn Face `cnb_cpf_cr`, VOLT `cnb_volt_cr`.  
Complex Cognition: PVRT `cnb_pvrt_cr`, PMAT `cnb_pmat_cr`, PLOT `cnb_plot_cr`, Digit Symbol `cnb_digsym_dscor`.  
Social Cognition: ER40 `cnb_er40_cr`, MEDF `cnb_medf_cr`, ADT `cnb_adt_cr`.  
Sensorimotor Performance: finger tapping `cnb_ctap_dom`, Motor Praxis `cnb_mpract_mp2`, Trails A `cnb_trails_rt`.

Alternatives: PCET may belong with complex cognition; Digit Symbol and Trails may be treated as processing-speed/sensorimotor indicators; AIM may require a narrower construct review. Discounting tasks remain separate.

## Transformations and profile summaries

Candidate later transformations are within-analytic-sample standardization after a frozen direction map, or norm-based standardization if an appropriate reference is justified. Age adjustment, cross-fitting, weighting, and transformation choice are intentionally unresolved. Global level, within-person profile shape, and scatter should be defined as distinct summaries. A profile with changing domain availability can change meaning because its level and shape may be based on different task subsets; availability must therefore be reported alongside any later profile.
